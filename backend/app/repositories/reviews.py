"""Queries for reviews and comments."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Comment, Review


def get_review(session: Session, review_id: uuid.UUID) -> Review | None:
    stmt = select(Review).options(selectinload(Review.assignments)).where(Review.id == review_id)
    return session.execute(stmt).scalar_one_or_none()


def latest_review_for_item(session: Session, item_id: uuid.UUID) -> Review | None:
    stmt = (
        select(Review)
        .options(selectinload(Review.assignments))
        .where(Review.item_id == item_id)
        .order_by(Review.created_at.desc())
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def comments_for_item(session: Session, item_id: uuid.UUID) -> list[Comment]:
    stmt = select(Comment).where(Comment.item_id == item_id).order_by(Comment.created_at)
    return list(session.execute(stmt).scalars().all())
