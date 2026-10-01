"""Queries for baselines and their entries."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Baseline, BaselineEntry, Item, ItemRevision, Project


def subtree_project_ids(session: Session, root_id: uuid.UUID) -> list[uuid.UUID]:
    """The root project plus all descendant projects (BFS over parent_id)."""
    all_projects = session.execute(select(Project.id, Project.parent_id)).all()
    children: dict[uuid.UUID, list[uuid.UUID]] = {}
    for pid, parent in all_projects:
        if parent is not None:
            children.setdefault(parent, []).append(pid)
    ids: list[uuid.UUID] = []
    frontier = [root_id]
    while frontier:
        current = frontier.pop()
        ids.append(current)
        frontier.extend(children.get(current, []))
    return ids


def list_baselines(session: Session, project_id: uuid.UUID) -> list[tuple[Baseline, int]]:
    count = (
        select(BaselineEntry.baseline_id, func.count(BaselineEntry.id).label("n"))
        .group_by(BaselineEntry.baseline_id)
        .subquery()
    )
    stmt = (
        select(Baseline, func.coalesce(count.c.n, 0))
        .outerjoin(count, count.c.baseline_id == Baseline.id)
        .where(Baseline.project_id == project_id)
        .order_by(Baseline.created_at.desc())
    )
    return [(b, n) for b, n in session.execute(stmt).all()]


def get_baseline(session: Session, baseline_id: uuid.UUID) -> Baseline | None:
    return session.get(Baseline, baseline_id)


def get_baseline_by_name(session: Session, project_id: uuid.UUID, name: str) -> Baseline | None:
    stmt = select(Baseline).where(Baseline.project_id == project_id, Baseline.name == name)
    return session.execute(stmt).scalar_one_or_none()


def baseline_entries(
    session: Session, baseline_id: uuid.UUID
) -> list[tuple[uuid.UUID, str, str, int]]:
    """Return (item_id, human_id, title, rev_number) for each entry."""
    stmt = (
        select(Item.id, Item.human_id, ItemRevision.title, ItemRevision.rev_number)
        .join(BaselineEntry, BaselineEntry.item_id == Item.id)
        .join(ItemRevision, ItemRevision.id == BaselineEntry.revision_id)
        .where(BaselineEntry.baseline_id == baseline_id)
        .order_by(Item.human_id)
    )
    return [(iid, hid, title, rev) for iid, hid, title, rev in session.execute(stmt).all()]
