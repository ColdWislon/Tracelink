"""Schemas for the evidence catalog and regression ingestion."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EvidenceKind


class EvidenceCreate(BaseModel):
    """Manually add a catalog entry (e.g. planned evidence not yet in Git)."""

    kind: EvidenceKind
    fqn: str = Field(min_length=1, max_length=400)
    name: str | None = None


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    kind: EvidenceKind
    fqn: str
    name: str
    in_git: bool
    in_regression: bool
    link_count: int = 0
    # Latest-run metrics (populated per kind) and derived state.
    passed: int | None = None
    failed: int | None = None
    total: int | None = None
    hits: int | None = None
    goal: int | None = None
    fired: int | None = None
    ran: bool = False
    satisfied: bool = False


# --- regression ingestion payload (documented via JSON Schema) ---------------


class RegressionResultIn(BaseModel):
    """One normalized evidence result. Fields are populated per ``kind``."""

    kind: EvidenceKind
    fqn: str
    name: str | None = None
    passed: int | None = Field(default=None, ge=0)
    failed: int | None = Field(default=None, ge=0)
    total: int | None = Field(default=None, ge=0)
    hits: int | None = Field(default=None, ge=0)
    goal: int | None = Field(default=None, ge=0)
    fired: int | None = Field(default=None, ge=0)


class RegressionRunIn(BaseModel):
    """A regression/coverage import payload pushed by rtrack-push or CI."""

    project_key: str
    source: str = "jenkins"
    external_id: str | None = None
    label: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    results: list[RegressionResultIn]


class RegressionRunAccepted(BaseModel):
    run_id: uuid.UUID
    project_key: str
    result_count: int
    created_evidence: int
