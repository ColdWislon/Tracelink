"""Item CRUD orchestration: identity, immutable revisions, attribute validation,
EARS pattern detection, audit logging, and read-model assembly."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models import AuditLog, Item, ItemRevision, Link
from app.models.enums import VerificationStatus
from app.repositories import items as item_repo
from app.repositories import projects as project_repo
from app.repositories import reviews as review_repo
from app.schemas.item import ItemCreate, ItemDetail, ItemRead, ItemUpdate, LinkRef, RevisionRead
from app.schemas.review import CommentRead, ReviewRead
from app.services import status_service
from app.services.domain.attributes import normalize_attributes, validate_attributes
from app.services.domain.ears import detect_pattern
from app.services.domain.ids import format_human_id, next_sequence
from app.services.domain.links import link_is_suspect
from app.services.domain.revisions import content_changed, next_rev_number


class DomainError(ValueError):
    """A business-rule violation (mapped to HTTP 422 at the API boundary)."""


def _audit(
    session: Session, entity_id: uuid.UUID, action: str, actor: str, **detail: object
) -> None:
    session.add(
        AuditLog(entity_type="item", entity_id=entity_id, action=action, actor=actor, detail=detail)
    )


def create_item(session: Session, payload: ItemCreate, author: str) -> Item:
    project = project_repo.get_project(session, payload.project_id)
    if project is None:
        raise DomainError("project not found")
    item_type = project_repo.get_item_type(session, payload.item_type_id)
    if item_type is None:
        raise DomainError("item type not found")

    errors = validate_attributes(item_type.attribute_schema, payload.attributes)
    if errors:
        raise DomainError("; ".join(f"{e.key}: {e.message}" for e in errors))
    attributes = normalize_attributes(item_type.attribute_schema, payload.attributes)

    seq = next_sequence(item_repo.max_seq(session, project.id, item_type.id))
    human_id = format_human_id(item_type.id_prefix, project.key, seq)

    item = Item(
        project_id=project.id,
        item_type_id=item_type.id,
        human_id=human_id,
        seq=seq,
        workflow_status=payload.workflow_status,
        applicability=payload.applicability,
    )
    session.add(item)
    session.flush()

    revision = ItemRevision(
        item_id=item.id,
        rev_number=1,
        title=payload.title,
        body=payload.body,
        attributes=attributes,
        ears_pattern=detect_pattern(payload.body or payload.title),
        author=author,
        message=payload.message or "Created",
    )
    session.add(revision)
    session.flush()
    item.current_revision_id = revision.id
    _audit(session, item.id, "create", author, human_id=human_id)
    session.flush()
    return item


def update_item(session: Session, item_id: uuid.UUID, payload: ItemUpdate, author: str) -> Item:
    item = item_repo.get_item(session, item_id)
    if item is None or item.current_revision is None:
        raise DomainError("item not found")
    current = item.current_revision

    new_title = payload.title if payload.title is not None else current.title
    new_body = payload.body if payload.body is not None else current.body
    new_attributes = payload.attributes if payload.attributes is not None else current.attributes

    if payload.attributes is not None:
        errors = validate_attributes(item.item_type.attribute_schema, new_attributes)
        if errors:
            raise DomainError("; ".join(f"{e.key}: {e.message}" for e in errors))
        new_attributes = normalize_attributes(item.item_type.attribute_schema, new_attributes)

    if content_changed(
        current.title, current.body, current.attributes, new_title, new_body, new_attributes
    ):
        revision = ItemRevision(
            item_id=item.id,
            rev_number=next_rev_number(item_repo.max_rev_number(session, item.id)),
            title=new_title,
            body=new_body,
            attributes=new_attributes,
            ears_pattern=detect_pattern(new_body or new_title),
            author=author,
            message=payload.message or "Edited",
        )
        session.add(revision)
        session.flush()
        item.current_revision_id = revision.id
        _audit(session, item.id, "revise", author, rev=revision.rev_number)

    if payload.workflow_status is not None:
        item.workflow_status = payload.workflow_status
        _audit(session, item.id, "workflow", author, status=payload.workflow_status.value)
    if payload.applicability is not None:
        item.applicability = payload.applicability

    session.flush()
    return item


# --- read-model assembly -----------------------------------------------------


def _link_refs(
    items: list[Item], links: list[Link], statuses: dict[uuid.UUID, VerificationStatus]
) -> tuple[dict[uuid.UUID, list[LinkRef]], dict[uuid.UUID, list[LinkRef]]]:
    """Build per-item upstream/downstream link references with suspect flags."""
    upstream: dict[uuid.UUID, list[LinkRef]] = {i.id: [] for i in items}
    downstream: dict[uuid.UUID, list[LinkRef]] = {i.id: [] for i in items}

    for link in links:
        suspect = link_is_suspect(
            link.upstream_item.current_revision_id, link.reviewed_upstream_revision_id
        )
        # Downstream endpoint, as seen from the upstream item.
        if link.upstream_item_id in downstream:
            if link.downstream_item is not None:
                di = link.downstream_item
                downstream[link.upstream_item_id].append(
                    LinkRef(
                        link_id=link.id,
                        link_type=link.link_type,
                        target="item",
                        id=di.id,
                        human_id=di.human_id,
                        title=di.current_revision.title if di.current_revision else "",
                        suspect=suspect,
                        base_kind=di.item_type.base_kind,
                        status=statuses.get(di.id),
                    )
                )
            elif link.downstream_evidence is not None:
                ev = link.downstream_evidence
                downstream[link.upstream_item_id].append(
                    LinkRef(
                        link_id=link.id,
                        link_type=link.link_type,
                        target="evidence",
                        id=ev.id,
                        human_id=ev.fqn,
                        title=ev.name,
                        suspect=False,
                        evidence_kind=ev.kind,
                    )
                )
        # Upstream endpoint, as seen from the downstream item.
        if link.downstream_item_id in upstream:
            up = link.upstream_item
            upstream[link.downstream_item_id].append(
                LinkRef(
                    link_id=link.id,
                    link_type=link.link_type,
                    target="item",
                    id=up.id,
                    human_id=up.human_id,
                    title=up.current_revision.title if up.current_revision else "",
                    suspect=suspect,
                    base_kind=up.item_type.base_kind,
                    status=statuses.get(up.id),
                )
            )
    return upstream, downstream


def _to_read(
    item: Item,
    status: VerificationStatus | None,
    upstream: list[LinkRef],
    downstream: list[LinkRef],
) -> ItemRead:
    rev = item.current_revision
    return ItemRead(
        id=item.id,
        human_id=item.human_id,
        project_id=item.project_id,
        project_key=item.project.key,
        item_type_id=item.item_type_id,
        type_key=item.item_type.key,
        base_kind=item.item_type.base_kind,
        title=rev.title if rev else "",
        body=rev.body if rev else "",
        attributes=rev.attributes if rev else {},
        ears_pattern=rev.ears_pattern if rev else None,
        workflow_status=item.workflow_status,
        applicability=item.applicability,
        rev_number=rev.rev_number if rev else 0,
        current_revision_id=item.current_revision_id,
        status=status,
        upstream=upstream,
        downstream=downstream,
    )


def list_item_reads(session: Session, project_id: uuid.UUID) -> list[ItemRead]:
    items = item_repo.list_items(session, project_id)
    statuses = status_service.compute_statuses(session, project_id)
    links = item_repo.links_for_items(session, [i.id for i in items])
    upstream, downstream = _link_refs(items, links, statuses)
    return [
        _to_read(i, statuses.get(i.id), upstream.get(i.id, []), downstream.get(i.id, []))
        for i in items
    ]


def get_item_read(session: Session, item_id: uuid.UUID) -> ItemDetail | None:
    item = item_repo.get_item_with_revisions(session, item_id)
    if item is None:
        return None
    statuses = status_service.compute_statuses(session, item.project_id)
    links = item_repo.links_for_items(session, [item.id])
    upstream, downstream = _link_refs([item], links, statuses)
    base = _to_read(
        item, statuses.get(item.id), upstream.get(item.id, []), downstream.get(item.id, [])
    )
    review = review_repo.latest_review_for_item(session, item.id)
    comments = review_repo.comments_for_item(session, item.id)
    return ItemDetail(
        **base.model_dump(),
        revisions=[
            RevisionRead.model_validate(r)
            for r in sorted(item.revisions, key=lambda r: r.rev_number, reverse=True)
        ],
        review=ReviewRead.model_validate(review) if review else None,
        comments=[CommentRead.model_validate(c) for c in comments],
    )
