"""Baseline orchestration: snapshot a project subtree's current revisions."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, Baseline, BaselineEntry, Item
from app.repositories import baselines as baseline_repo
from app.repositories import projects as project_repo
from app.schemas.baseline import BaselineCreate, BaselineDetail, BaselineEntryRead, BaselineRead
from app.services.item_service import DomainError


def _to_read(baseline: Baseline, entry_count: int) -> BaselineRead:
    return BaselineRead(
        id=baseline.id,
        project_id=baseline.project_id,
        name=baseline.name,
        milestone=baseline.milestone,
        description=baseline.description,
        frozen=baseline.frozen,
        created_by=baseline.created_by,
        created_at=baseline.created_at,
        entry_count=entry_count,
    )


def create_baseline(
    session: Session, project_id: uuid.UUID, payload: BaselineCreate, author: str
) -> BaselineDetail:
    if project_repo.get_project(session, project_id) is None:
        raise DomainError("project not found")
    if baseline_repo.get_baseline_by_name(session, project_id, payload.name) is not None:
        raise DomainError(f"a baseline named '{payload.name}' already exists")

    project_ids = baseline_repo.subtree_project_ids(session, project_id)
    items = list(
        session.execute(
            select(Item).where(
                Item.project_id.in_(project_ids), Item.current_revision_id.is_not(None)
            )
        )
        .scalars()
        .all()
    )

    baseline = Baseline(
        project_id=project_id,
        name=payload.name,
        milestone=payload.milestone,
        description=payload.description,
        frozen=True,
        created_by=author,
    )
    session.add(baseline)
    session.flush()
    for item in items:
        session.add(
            BaselineEntry(
                baseline_id=baseline.id,
                item_id=item.id,
                revision_id=item.current_revision_id,
            )
        )
    session.add(
        AuditLog(
            entity_type="baseline",
            entity_id=baseline.id,
            action="create",
            actor=author,
            detail={"name": payload.name, "items": len(items)},
        )
    )
    session.flush()
    return get_baseline_detail(session, baseline.id)  # type: ignore[return-value]


def list_baselines(session: Session, project_id: uuid.UUID) -> list[BaselineRead]:
    return [
        _to_read(baseline, count)
        for baseline, count in baseline_repo.list_baselines(session, project_id)
    ]


def get_baseline_detail(session: Session, baseline_id: uuid.UUID) -> BaselineDetail | None:
    baseline = baseline_repo.get_baseline(session, baseline_id)
    if baseline is None:
        return None
    rows = baseline_repo.baseline_entries(session, baseline_id)
    base = _to_read(baseline, len(rows))
    return BaselineDetail(
        **base.model_dump(),
        entries=[
            BaselineEntryRead(item_id=iid, human_id=hid, title=title, rev_number=rev)
            for iid, hid, title, rev in rows
        ],
    )
