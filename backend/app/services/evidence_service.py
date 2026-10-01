"""Evidence catalog assembly: attach latest-run metrics and derived state."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models import Evidence
from app.models.enums import EvidenceKind
from app.repositories import evidence as evidence_repo
from app.repositories import projects as project_repo
from app.schemas.evidence import EvidenceRead
from app.services.domain.status import EvidenceOutcome, EvidenceState, evidence_state
from app.services.item_service import DomainError


def create_evidence(
    session: Session, project_id: uuid.UUID, kind: EvidenceKind, fqn: str, name: str | None
) -> EvidenceRead:
    """Add a catalog entry by hand (in_git/in_regression both false). Idempotent."""
    if project_repo.get_project(session, project_id) is None:
        raise DomainError("project not found")
    fqn = fqn.strip()
    if not fqn:
        raise DomainError("fqn is required")

    evidence = evidence_repo.get_evidence_by_identity(session, project_id, kind, fqn)
    if evidence is None:
        evidence = Evidence(
            project_id=project_id,
            kind=kind,
            fqn=fqn,
            name=(name or fqn).strip(),
            in_git=False,
            in_regression=False,
        )
        session.add(evidence)
        session.flush()

    counts = evidence_repo.evidence_link_counts(session, project_id)
    return EvidenceRead(
        id=evidence.id,
        project_id=evidence.project_id,
        kind=evidence.kind,
        fqn=evidence.fqn,
        name=evidence.name,
        in_git=evidence.in_git,
        in_regression=evidence.in_regression,
        link_count=counts.get(evidence.id, 0),
    )


def list_catalog(session: Session, project_id: uuid.UUID) -> list[EvidenceRead]:
    evidence = evidence_repo.list_evidence(session, project_id)
    counts = evidence_repo.evidence_link_counts(session, project_id)
    run = evidence_repo.latest_run_in_hierarchy(session, project_id)
    results = evidence_repo.results_for_run(session, run.id) if run else {}

    catalog: list[EvidenceRead] = []
    for ev in evidence:
        result = results.get(ev.id)
        state: EvidenceState = (
            evidence_state(
                EvidenceOutcome(
                    kind=ev.kind,
                    passed=result.passed,
                    failed=result.failed,
                    total=result.total,
                    hits=result.hits,
                    goal=result.goal,
                    fired=result.fired,
                )
            )
            if result
            else EvidenceState(ran=False, satisfied=False, failing=False)
        )
        catalog.append(
            EvidenceRead(
                id=ev.id,
                project_id=ev.project_id,
                kind=ev.kind,
                fqn=ev.fqn,
                name=ev.name,
                in_git=ev.in_git,
                in_regression=ev.in_regression,
                link_count=counts.get(ev.id, 0),
                passed=result.passed if result else None,
                failed=result.failed if result else None,
                total=result.total if result else None,
                hits=result.hits if result else None,
                goal=result.goal if result else None,
                fired=result.fired if result else None,
                ran=state.ran,
                satisfied=state.satisfied,
            )
        )
    return catalog
