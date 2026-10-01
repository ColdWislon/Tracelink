"""Schema for the verification-closure dashboard summary."""

from __future__ import annotations

from pydantic import BaseModel

from app.models.enums import VerificationStatus
from app.schemas.evidence import RegressionRunRead


class StatusCounts(BaseModel):
    covered: int = 0
    partial: int = 0
    failing: int = 0
    not_run: int = 0
    uncovered: int = 0

    def add(self, status: VerificationStatus) -> None:
        setattr(self, status.value, getattr(self, status.value) + 1)

    @property
    def total(self) -> int:
        return self.covered + self.partial + self.failing + self.not_run + self.uncovered


class DashboardRead(BaseModel):
    requirements: StatusCounts
    verification_items: StatusCounts
    requirement_total: int
    covered_pct: float
    suspect_links: int
    orphan_requirements: int
    orphan_verification_items: int
    orphan_evidence: int
    latest_run: RegressionRunRead | None
