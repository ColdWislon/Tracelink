"""Named, frozen sets of (item, revision) pairs — one per milestone."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import Timestamped, UUIDpk


class Baseline(UUIDpk, Timestamped, Base):
    """A milestone snapshot (e.g. RTL freeze, tapeout)."""

    __tablename__ = "baseline"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_baseline_project_name"),)

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    milestone: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    frozen: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str | None] = mapped_column(String(200), nullable=True)

    entries: Mapped[list[BaselineEntry]] = relationship(
        back_populates="baseline", cascade="all, delete-orphan"
    )


class BaselineEntry(UUIDpk, Base):
    """Pins one item to a specific revision within a baseline."""

    __tablename__ = "baseline_entry"
    __table_args__ = (UniqueConstraint("baseline_id", "item_id", name="uq_baseline_entry_item"),)

    baseline_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("baseline.id", ondelete="CASCADE"), index=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("item.id", ondelete="CASCADE"))
    revision_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("item_revision.id", ondelete="RESTRICT")
    )

    baseline: Mapped[Baseline] = relationship(back_populates="entries")
