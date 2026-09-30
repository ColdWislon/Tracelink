"""Queries for evidence and regression results."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Evidence, EvidenceResult, Link, Project, RegressionRun
from app.models.enums import EvidenceKind, LinkType


def list_evidence(session: Session, project_id: uuid.UUID) -> list[Evidence]:
    stmt = (
        select(Evidence)
        .where(Evidence.project_id == project_id)
        .order_by(Evidence.kind, Evidence.fqn)
    )
    return list(session.execute(stmt).scalars().all())


def get_evidence_by_identity(
    session: Session, project_id: uuid.UUID, kind: EvidenceKind, fqn: str
) -> Evidence | None:
    stmt = select(Evidence).where(
        Evidence.project_id == project_id, Evidence.kind == kind, Evidence.fqn == fqn
    )
    return session.execute(stmt).scalar_one_or_none()


def evidence_link_counts(session: Session, project_id: uuid.UUID) -> dict[uuid.UUID, int]:
    stmt = (
        select(Link.downstream_evidence_id, func.count(Link.id))
        .where(Link.link_type == LinkType.EVIDENCED_BY, Link.downstream_evidence_id.is_not(None))
        .group_by(Link.downstream_evidence_id)
    )
    return {eid: count for eid, count in session.execute(stmt).all() if eid is not None}


def latest_run(session: Session, project_id: uuid.UUID) -> RegressionRun | None:
    stmt = (
        select(RegressionRun)
        .where(RegressionRun.project_id == project_id)
        .order_by(
            func.coalesce(RegressionRun.finished_at, RegressionRun.imported_at).desc().nulls_last(),
            RegressionRun.created_at.desc(),
        )
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def latest_run_in_hierarchy(session: Session, project_id: uuid.UUID) -> RegressionRun | None:
    """Latest run for the project, falling back to ancestor (SoC) runs.

    Runs are often recorded at the SoC level but cover evidence in child IP
    projects, so lookups for an IP walk up the project tree.
    """
    current: uuid.UUID | None = project_id
    while current is not None:
        run = latest_run(session, current)
        if run is not None:
            return run
        project = session.get(Project, current)
        current = project.parent_id if project else None
    return None


def results_for_run(session: Session, run_id: uuid.UUID) -> dict[uuid.UUID, EvidenceResult]:
    stmt = select(EvidenceResult).where(EvidenceResult.run_id == run_id)
    return {r.evidence_id: r for r in session.execute(stmt).scalars().all()}
