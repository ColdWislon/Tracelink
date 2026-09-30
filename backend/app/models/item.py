"""Items, their immutable revisions, and typed links between them."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import LinkType, WorkflowStatus
from app.models.mixins import Timestamped, UUIDpk

if TYPE_CHECKING:
    from app.models.evidence import Evidence
    from app.models.project import ItemType, Project


class Item(UUIDpk, Timestamped, Base):
    """Identity + workflow for a requirement or verification item.

    Content (title, body, attributes) is versioned in :class:`ItemRevision`;
    ``current_revision_id`` points at the live revision.
    """

    __tablename__ = "item"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    item_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("item_type.id", ondelete="RESTRICT"))
    human_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    seq: Mapped[int] = mapped_column(Integer)
    workflow_status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus, native_enum=False, length=32), default=WorkflowStatus.DRAFT
    )
    # Variant applicability expression over variant keys, e.g. "A0 | A1-lite".
    # Null means the item applies to every variant.
    applicability: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("item_revision.id", use_alter=True, name="fk_item_current_revision"),
        nullable=True,
    )

    project: Mapped[Project] = relationship(back_populates="items")
    item_type: Mapped[ItemType] = relationship()
    revisions: Mapped[list[ItemRevision]] = relationship(
        back_populates="item",
        foreign_keys="ItemRevision.item_id",
        cascade="all, delete-orphan",
        order_by="ItemRevision.rev_number",
    )
    current_revision: Mapped[ItemRevision | None] = relationship(
        foreign_keys=[current_revision_id], post_update=True
    )


class ItemRevision(UUIDpk, Base):
    """An immutable snapshot of an item's content. Never updated in place."""

    __tablename__ = "item_revision"
    __table_args__ = (UniqueConstraint("item_id", "rev_number", name="uq_revision_item_number"),)

    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("item.id", ondelete="CASCADE"), index=True
    )
    rev_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text, default="")
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    # EARS pattern label (e.g. "Event-driven"); may be auto-detected on save.
    ears_pattern: Mapped[str | None] = mapped_column(String(64), nullable=True)
    author: Mapped[str] = mapped_column(String(200))
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    item: Mapped[Item] = relationship(back_populates="revisions", foreign_keys=[item_id])


class Link(UUIDpk, Timestamped, Base):
    """A typed, directional traceability link.

    ``upstream_item`` is the source of truth whose change makes the link *suspect*;
    the downstream endpoint is either another item or a piece of evidence
    (evidenced_by). ``reviewed_upstream_revision_id`` records the upstream revision
    the link was last reviewed against.
    """

    __tablename__ = "link"
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(downstream_item_id, downstream_evidence_id) = 1",
            name="ck_link_single_downstream",
        ),
        UniqueConstraint(
            "link_type",
            "upstream_item_id",
            "downstream_item_id",
            "downstream_evidence_id",
            name="uq_link_endpoints",
        ),
    )

    link_type: Mapped[LinkType] = mapped_column(Enum(LinkType, native_enum=False, length=32))
    upstream_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("item.id", ondelete="CASCADE"), index=True
    )
    downstream_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("item.id", ondelete="CASCADE"), nullable=True, index=True
    )
    downstream_evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("evidence.id", ondelete="CASCADE"), nullable=True, index=True
    )
    reviewed_upstream_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("item_revision.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[str | None] = mapped_column(String(200), nullable=True)

    upstream_item: Mapped[Item] = relationship(foreign_keys=[upstream_item_id])
    downstream_item: Mapped[Item | None] = relationship(foreign_keys=[downstream_item_id])
    downstream_evidence: Mapped[Evidence | None] = relationship(
        foreign_keys=[downstream_evidence_id]
    )
    reviewed_upstream_revision: Mapped[ItemRevision | None] = relationship(
        foreign_keys=[reviewed_upstream_revision_id]
    )
