"""Evidence catalog and normalized regression/coverage results."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import EvidenceKind
from app.models.mixins import Timestamped, UUIDpk


class Evidence(UUIDpk, Timestamped, Base):
    """A catalog entry for a test, coverpoint, or assertion.

    Provenance flags record whether the entry was seen in the Git testbench and/or
    in regression results; a mismatch (e.g. in regression but not Git) is surfaced
    in the UI.
    """

    __tablename__ = "evidence"
    __table_args__ = (UniqueConstraint("project_id", "kind", "fqn", name="uq_evidence_identity"),)

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[EvidenceKind] = mapped_column(Enum(EvidenceKind, native_enum=False, length=32))
    fqn: Mapped[str] = mapped_column(String(400), index=True)
    name: Mapped[str] = mapped_column(String(400))
    in_git: Mapped[bool] = mapped_column(Boolean, default=False)
    in_regression: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen_git_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_seen_regression_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Scanner metadata: source file, class name, covergroup, etc.
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    results: Mapped[list[EvidenceResult]] = relationship(
        back_populates="evidence", cascade="all, delete-orphan"
    )


class RegressionRun(UUIDpk, Timestamped, Base):
    """A single regression/coverage import (e.g. a Jenkins build / vManager session)."""

    __tablename__ = "regression_run"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    source: Mapped[str] = mapped_column(String(120))
    external_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    results: Mapped[list[EvidenceResult]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class EvidenceResult(UUIDpk, Base):
    """A normalized result for one evidence item in one run.

    Columns are populated per evidence kind (``kind`` disambiguates):
      - test:      ``passed`` / ``failed`` / ``total``
      - coverpoint: ``hits`` (reached) vs ``goal``
      - assertion:  ``fired`` count and ``failed`` count
    Raw payload is retained in ``meta``. Status is derived by pure domain logic,
    not stored here.
    """

    __tablename__ = "evidence_result"
    __table_args__ = (UniqueConstraint("run_id", "evidence_id", name="uq_result_run_evidence"),)

    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("regression_run.id", ondelete="CASCADE"), index=True
    )
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[EvidenceKind] = mapped_column(Enum(EvidenceKind, native_enum=False, length=32))

    passed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hits: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fired: Mapped[int | None] = mapped_column(Integer, nullable=True)

    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    run: Mapped[RegressionRun] = relationship(back_populates="results")
    evidence: Mapped[Evidence] = relationship(back_populates="results")
