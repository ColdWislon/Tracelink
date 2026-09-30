"""Project hierarchy, variants, reusable-IP references, and item types."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import ItemBaseKind, ProjectKind
from app.models.mixins import Timestamped, UUIDpk

if TYPE_CHECKING:
    from app.models.item import Item


class Project(UUIDpk, Timestamped, Base):
    """A SoC, subsystem, or IP/block. Forms a containment tree via ``parent_id``."""

    __tablename__ = "project"

    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[ProjectKind] = mapped_column(Enum(ProjectKind, native_enum=False, length=32))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("project.id", ondelete="SET NULL"), nullable=True
    )
    # Marks a reusable IP that other projects reference at a pinned version.
    is_ip_library: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    parent: Mapped[Project | None] = relationship(
        remote_side="Project.id", back_populates="children"
    )
    children: Mapped[list[Project]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
    variants: Mapped[list[Variant]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    item_types: Mapped[list[ItemType]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    items: Mapped[list[Item]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Variant(UUIDpk, Timestamped, Base):
    """A chip variant/derivative (e.g. A0, A1-lite). Applicability lives on items."""

    __tablename__ = "variant"
    __table_args__ = (UniqueConstraint("project_id", "key", name="uq_variant_project_key"),)

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    key: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship(back_populates="variants")


class IpReference(UUIDpk, Timestamped, Base):
    """A consumer project's reuse of a library IP project, pinned to a version."""

    __tablename__ = "ip_reference"

    consumer_project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    ip_project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("project.id", ondelete="RESTRICT"))
    instance_name: Mapped[str] = mapped_column(String(120))
    # A tag or baseline name identifying the pinned version of the IP.
    pinned_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    pinned_baseline_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("baseline.id", ondelete="SET NULL"), nullable=True
    )


class ItemType(UUIDpk, Timestamped, Base):
    """Defines a category of item: its ID prefix, base kind, and attribute schema.

    ``attribute_schema`` is a list of field definitions, each a dict with keys such
    as ``key``, ``label``, ``type`` (string/text/number/enum/bool), ``required``,
    ``options`` (for enums), and ``default``. It validates ``Item`` attributes.
    A null ``project_id`` marks a global/library type reusable across projects.
    """

    __tablename__ = "item_type"
    __table_args__ = (UniqueConstraint("project_id", "key", name="uq_item_type_project_key"),)

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), nullable=True, index=True
    )
    key: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(200))
    base_kind: Mapped[ItemBaseKind] = mapped_column(
        Enum(ItemBaseKind, native_enum=False, length=32)
    )
    id_prefix: Mapped[str] = mapped_column(String(16))
    attribute_schema: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped[Project | None] = relationship(back_populates="item_types")
