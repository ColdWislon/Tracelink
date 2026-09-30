"""Link orchestration: create typed links, delete them, and clear suspect flags."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models import AuditLog, Evidence, Link
from app.models.enums import LinkType
from app.repositories import items as item_repo
from app.repositories import links as link_repo
from app.schemas.link import LinkCreate, LinkCreated
from app.services.domain.links import link_is_suspect
from app.services.item_service import DomainError


def _audit(session: Session, link_id: uuid.UUID, action: str, actor: str, **detail: object) -> None:
    session.add(
        AuditLog(entity_type="link", entity_id=link_id, action=action, actor=actor, detail=detail)
    )


def _to_created(link: Link) -> LinkCreated:
    suspect = link_is_suspect(
        link.upstream_item.current_revision_id, link.reviewed_upstream_revision_id
    )
    return LinkCreated(
        link_id=link.id,
        link_type=link.link_type,
        upstream_item_id=link.upstream_item_id,
        downstream_item_id=link.downstream_item_id,
        downstream_evidence_id=link.downstream_evidence_id,
        suspect=suspect,
    )


def create_link(session: Session, payload: LinkCreate, author: str) -> LinkCreated:
    upstream = item_repo.get_item(session, payload.upstream_item_id)
    if upstream is None:
        raise DomainError("upstream item not found")

    if payload.downstream_item_id is not None:
        if item_repo.get_item(session, payload.downstream_item_id) is None:
            raise DomainError("downstream item not found")
        if payload.downstream_item_id == payload.upstream_item_id:
            raise DomainError("cannot link an item to itself")
    elif payload.downstream_evidence_id is not None:
        if session.get(Evidence, payload.downstream_evidence_id) is None:
            raise DomainError("downstream evidence not found")

    existing = link_repo.find_link(
        session,
        payload.link_type,
        payload.upstream_item_id,
        payload.downstream_item_id,
        payload.downstream_evidence_id,
    )
    if existing is not None:
        return _to_created(existing)

    # Item->item links baseline against the upstream's current revision so a later
    # upstream change makes the link suspect. Evidence links carry no baseline.
    reviewed = upstream.current_revision_id if payload.downstream_item_id is not None else None
    link = Link(
        link_type=payload.link_type,
        upstream_item_id=payload.upstream_item_id,
        downstream_item_id=payload.downstream_item_id,
        downstream_evidence_id=payload.downstream_evidence_id,
        reviewed_upstream_revision_id=reviewed,
        created_by=author,
    )
    session.add(link)
    session.flush()
    _audit(session, link.id, "create", author, link_type=payload.link_type.value)
    return _to_created(link)


def delete_link(session: Session, link_id: uuid.UUID, author: str) -> None:
    link = link_repo.get_link(session, link_id)
    if link is None:
        raise DomainError("link not found")
    _audit(session, link.id, "delete", author)
    session.delete(link)
    session.flush()


def clear_suspect(session: Session, link_id: uuid.UUID, author: str) -> LinkCreated:
    link = link_repo.get_link(session, link_id)
    if link is None:
        raise DomainError("link not found")
    if link.link_type == LinkType.EVIDENCED_BY:
        raise DomainError("evidence links do not carry a suspect baseline")
    # Re-pin the reviewed baseline to the upstream's current revision.
    link.reviewed_upstream_revision_id = link.upstream_item.current_revision_id
    _audit(session, link.id, "clear_suspect", author)
    session.flush()
    return _to_created(link)
