"""Ingest a normalized regression/coverage payload into a RegressionRun.

This is the server side of the Phase 3 pipeline; it is functional now so the
seeded run drives statuses and so ``rtrack-push`` has a real target.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import Evidence, EvidenceResult, RegressionRun
from app.repositories import evidence as evidence_repo
from app.repositories import projects as project_repo
from app.schemas.evidence import RegressionRunAccepted, RegressionRunIn
from app.services.item_service import DomainError


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
