"""Ingest a normalized regression/coverage payload into a RegressionRun.

This is the server side of the Phase 3 pipeline; it is functional now so the
seeded run drives statuses and so ``rtrack-push`` has a real target.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import Evidence, EvidenceResult, RegressionRun
from app.models.enums import EvidenceKind
from app.repositories import evidence as evidence_repo
from app.repositories import projects as project_repo
from app.schemas.evidence import (
    KindSummary,
    RegressionRunAccepted,
    RegressionRunIn,
    RegressionRunRead,
)
from app.services.domain.status import EvidenceOutcome, evidence_state
from app.services.item_service import DomainError

_KIND_FIELD = {
    EvidenceKind.TEST: "tests",
    EvidenceKind.COVERPOINT: "coverpoints",
    EvidenceKind.ASSERTION: "assertions",
}


def _summarize(session: Session, run: RegressionRun) -> RegressionRunRead:
    results = evidence_repo.results_for_run(session, run.id)
    buckets = {
        "tests": KindSummary(),
        "coverpoints": KindSummary(),
        "assertions": KindSummary(),
    }
    for result in results.values():
        bucket = buckets[_KIND_FIELD[result.kind]]
        bucket.total += 1
        state = evidence_state(
            EvidenceOutcome(
                kind=result.kind,
                passed=result.passed,
                failed=result.failed,
                total=result.total,
                hits=result.hits,
                goal=result.goal,
                fired=result.fired,
            )
        )
        if state.failing:
            bucket.failing += 1
        elif not state.ran:
            bucket.not_run += 1
        elif state.satisfied:
            bucket.satisfied += 1
        else:
            bucket.partial += 1
    return RegressionRunRead(
        id=run.id,
        project_id=run.project_id,
        source=run.source,
        external_id=run.external_id,
        label=run.label,
        started_at=run.started_at,
        finished_at=run.finished_at,
        imported_at=run.imported_at,
        result_count=len(results),
        tests=buckets["tests"],
        coverpoints=buckets["coverpoints"],
        assertions=buckets["assertions"],
    )


def list_runs(session: Session, project_id: uuid.UUID) -> list[RegressionRunRead]:
    return [
        _summarize(session, run) for run in evidence_repo.runs_in_hierarchy(session, project_id)
    ]


def get_run(session: Session, run_id: uuid.UUID) -> RegressionRunRead | None:
    run = evidence_repo.get_run(session, run_id)
    return _summarize(session, run) if run else None


def latest_run_summary(session: Session, project_id: uuid.UUID) -> RegressionRunRead | None:
    run = evidence_repo.latest_run_in_hierarchy(session, project_id)
    return _summarize(session, run) if run else None


def ingest_run(session: Session, payload: RegressionRunIn) -> RegressionRunAccepted:
    project = project_repo.get_project_by_key(session, payload.project_key)
    if project is None:
        raise DomainError(f"unknown project_key '{payload.project_key}'")

    now = datetime.now(UTC)
    run = RegressionRun(
        project_id=project.id,
        source=payload.source,
        external_id=payload.external_id,
        label=payload.label,
        started_at=payload.started_at,
        finished_at=payload.finished_at,
        imported_at=now,
    )
    session.add(run)
    session.flush()

    created_evidence = 0
    for result in payload.results:
        evidence = evidence_repo.get_evidence_by_identity(
            session, project.id, result.kind, result.fqn
        )
        if evidence is None:
            evidence = Evidence(
                project_id=project.id,
                kind=result.kind,
                fqn=result.fqn,
                name=result.name or result.fqn,
                in_regression=True,
                last_seen_regression_at=now,
            )
            session.add(evidence)
            session.flush()
            created_evidence += 1
        else:
            evidence.in_regression = True
            evidence.last_seen_regression_at = now

        session.add(
            EvidenceResult(
                run_id=run.id,
                evidence_id=evidence.id,
                kind=result.kind,
                passed=result.passed,
                failed=result.failed,
                total=result.total,
                hits=result.hits,
                goal=result.goal,
                fired=result.fired,
            )
        )

    session.flush()
    return RegressionRunAccepted(
        run_id=run.id,
        project_key=payload.project_key,
        result_count=len(payload.results),
        created_evidence=created_evidence,
    )
