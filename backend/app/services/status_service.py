"""Compute verification statuses for a project by combining links + latest run
results with the pure domain status functions."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models import EvidenceResult
from app.models.enums import ItemBaseKind, LinkType, VerificationStatus
from app.repositories import evidence as evidence_repo
from app.repositories import items as item_repo
from app.services.domain.status import (
    EvidenceOutcome,
    EvidenceState,
    evidence_state,
    rollup_requirement_status,
    verification_item_status,
)


def _outcome(result: EvidenceResult) -> EvidenceOutcome:
    return EvidenceOutcome(
        kind=result.kind,
        passed=result.passed,
        failed=result.failed,
        total=result.total,
        hits=result.hits,
        goal=result.goal,
        fired=result.fired,
    )


# An evidence result that never ran in the latest regression.
_NOT_RUN = EvidenceState(ran=False, satisfied=False, failing=False)


def compute_statuses(
    session: Session, project_id: uuid.UUID
) -> dict[uuid.UUID, VerificationStatus]:
    """Return a status for every requirement and verification item in the project."""
    items = item_repo.list_items(session, project_id)
    item_ids = [i.id for i in items]
    links = item_repo.links_for_items(session, item_ids)

    run = evidence_repo.latest_run_in_hierarchy(session, project_id)
    results = evidence_repo.results_for_run(session, run.id) if run else {}

    # Map each verification item to its linked evidence ids, and each requirement
    # to its verification items.
    vp_evidence: dict[uuid.UUID, list[uuid.UUID]] = {}
    req_vps: dict[uuid.UUID, list[uuid.UUID]] = {}
    for link in links:
        if link.link_type == LinkType.EVIDENCED_BY and link.downstream_evidence_id is not None:
            vp_evidence.setdefault(link.upstream_item_id, []).append(link.downstream_evidence_id)
        elif link.link_type == LinkType.VERIFIED_BY and link.downstream_item_id is not None:
            req_vps.setdefault(link.upstream_item_id, []).append(link.downstream_item_id)

    statuses: dict[uuid.UUID, VerificationStatus] = {}

    # Verification items first (requirements roll up from them).
    for item in items:
        if item.item_type.base_kind is not ItemBaseKind.VERIFICATION_ITEM:
            continue
        states: list[EvidenceState] = []
        for evidence_id in vp_evidence.get(item.id, []):
            result = results.get(evidence_id)
            states.append(evidence_state(_outcome(result)) if result else _NOT_RUN)
        statuses[item.id] = verification_item_status(states)

    for item in items:
        if item.item_type.base_kind is not ItemBaseKind.REQUIREMENT:
            continue
        vp_statuses = [statuses[vp] for vp in req_vps.get(item.id, []) if vp in statuses]
        statuses[item.id] = rollup_requirement_status(vp_statuses)

    return statuses
