"""Queries for projects, variants, and item types."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Item, ItemType, Project


def list_projects(session: Session) -> list[Project]:
    stmt = select(Project).options(selectinload(Project.variants)).order_by(Project.name)
    return list(session.execute(stmt).scalars().all())


def get_project(session: Session, project_id: uuid.UUID) -> Project | None:
    stmt = select(Project).options(selectinload(Project.variants)).where(Project.id == project_id)
    return session.execute(stmt).scalar_one_or_none()


def get_project_by_key(session: Session, key: str) -> Project | None:
    stmt = select(Project).where(Project.key == key)
    return session.execute(stmt).scalar_one_or_none()


def item_counts_by_project(session: Session) -> dict[uuid.UUID, int]:
    stmt = select(Item.project_id, func.count(Item.id)).group_by(Item.project_id)
    return dict(session.execute(stmt).all())


def list_item_types(session: Session, project_id: uuid.UUID | None = None) -> list[ItemType]:
    stmt = select(ItemType).order_by(ItemType.name)
    if project_id is not None:
        stmt = stmt.where(ItemType.project_id == project_id)
    return list(session.execute(stmt).scalars().all())


def get_item_type(session: Session, item_type_id: uuid.UUID) -> ItemType | None:
    return session.get(ItemType, item_type_id)
