"""Queries for items, revisions, and links."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Item, ItemRevision, Link


def get_item(session: Session, item_id: uuid.UUID) -> Item | None:
    stmt = (
        select(Item)
        .options(
            selectinload(Item.project),
            selectinload(Item.item_type),
            selectinload(Item.current_revision),
        )
        .where(Item.id == item_id)
    )
    return session.execute(stmt).scalar_one_or_none()


def get_item_with_revisions(session: Session, item_id: uuid.UUID) -> Item | None:
    stmt = (
        select(Item)
        .options(
            selectinload(Item.project),
            selectinload(Item.item_type),
            selectinload(Item.current_revision),
            selectinload(Item.revisions),
        )
        .where(Item.id == item_id)
    )
    return session.execute(stmt).scalar_one_or_none()


def list_items(session: Session, project_id: uuid.UUID | None = None) -> list[Item]:
    stmt = (
        select(Item)
        .options(
            selectinload(Item.project),
            selectinload(Item.item_type),
            selectinload(Item.current_revision),
        )
        .order_by(Item.human_id)
    )
    if project_id is not None:
        stmt = stmt.where(Item.project_id == project_id)
    return list(session.execute(stmt).scalars().all())


def max_seq(session: Session, project_id: uuid.UUID, item_type_id: uuid.UUID) -> int | None:
    stmt = select(func.max(Item.seq)).where(
        Item.project_id == project_id, Item.item_type_id == item_type_id
    )
    return session.execute(stmt).scalar_one()


def max_rev_number(session: Session, item_id: uuid.UUID) -> int | None:
    stmt = select(func.max(ItemRevision.rev_number)).where(ItemRevision.item_id == item_id)
    return session.execute(stmt).scalar_one()


def links_for_items(session: Session, item_ids: Sequence[uuid.UUID]) -> list[Link]:
    """All links whose upstream or downstream endpoint is one of ``item_ids``."""
    if not item_ids:
        return []
    ids = list(item_ids)
    stmt = (
        select(Link)
        .options(
            selectinload(Link.upstream_item).selectinload(Item.item_type),
            selectinload(Link.upstream_item).selectinload(Item.current_revision),
            selectinload(Link.downstream_item).selectinload(Item.item_type),
            selectinload(Link.downstream_item).selectinload(Item.current_revision),
            selectinload(Link.downstream_evidence),
        )
        .where(or_(Link.upstream_item_id.in_(ids), Link.downstream_item_id.in_(ids)))
    )
    return list(session.execute(stmt).scalars().all())
