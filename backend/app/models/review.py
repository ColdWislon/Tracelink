"""Review workflow, reviewer assignments, and comments."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import ReviewDecision, ReviewStatus
from app.models.mixins import Timestamped, UUIDpk


class Review(UUIDpk, Timestamped, Base):
    """A review of a specific item revision moving through an approval workflow."""

    __tablename__ = "review"

    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("item.id", ondelete="CASCADE"), index=True
    )
    revision_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("item_revision.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, native_enum=False, length=32), default=ReviewStatus.REQUESTED
    )
    requested_by: Mapped[str | None] = mapped_column(String(200), nullable=True)

    assignments: Mapped[list[ReviewAssignment]] = relationship(
        back_populates="review", cascade="all, delete-orphan"
    )


class ReviewAssignment(UUIDpk, Timestamped, Base):
    """One reviewer's decision on a review."""

    __tablename__ = "review_assignment"

    review_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("review.id", ondelete="CASCADE"), index=True
    )
    reviewer: Mapped[str] = mapped_column(String(200))
    role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    decision: Mapped[ReviewDecision] = mapped_column(
        Enum(ReviewDecision, native_enum=False, length=32), default=ReviewDecision.PENDING
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    review: Mapped[Review] = relationship(back_populates="assignments")


class Comment(UUIDpk, Timestamped, Base):
    """A discussion comment on an item (optionally tied to a review/revision)."""

    __tablename__ = "comment"

    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("item.id", ondelete="CASCADE"), index=True
    )
    review_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("review.id", ondelete="CASCADE"), nullable=True
    )
    revision_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("item_revision.id", ondelete="SET NULL"), nullable=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("comment.id", ondelete="CASCADE"), nullable=True
    )
    author: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
