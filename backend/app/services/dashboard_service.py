"""Verification-closure dashboard summary for a project."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.enums import ItemBaseKind, LinkType
from app.repositories import evidence as evidence_repo
from app.repositories import items as item_repo
from app.schemas.dashboard import DashboardRead, StatusCounts
from app.services import regression_service, status_service
from app.services.domain.links import link_is_suspect


def compute(session: Session, project_id: uuid.UUID) -> DashboardRead:
    items = item_repo.list_items(session, project_id)
    statuses = status_service.compute_statuses(session, project_id)
    links = item_repo.links_for_items(session, [i.id for i in items])

    req_counts = StatusCounts()
    vp_counts = StatusCounts()
    verified_reqs: set[uuid.UUID] = set()
    verified_vps: set[uuid.UUID] = set()
    for link in links:
        if link.link_type == LinkType.VERIFIED_BY and link.downstream_item_id is not None:
            verified_reqs.add(link.upstream_item_id)
            verified_vps.add(link.downstream_item_id)

    orphan_reqs = 0
    orphan_vps = 0
    for item in items:
        status = statuses.get(item.id)
        if item.item_type.base_kind is ItemBaseKind.REQUIREMENT:
            if status is not None:
                req_counts.add(status)
            if item.id not in verified_reqs:
                orphan_reqs += 1
        elif item.item_type.base_kind is ItemBaseKind.VERIFICATION_ITEM:
            if status is not None:
                vp_counts.add(status)
            if item.id not in verified_vps:
                orphan_vps += 1

    suspect_links = sum(
        1
        for link in links
        if link.downstream_item_id is not None
        and link_is_suspect(
            link.upstream_item.current_revision_id, link.reviewed_upstream_revision_id
        )
    )

    link_counts = evidence_repo.evidence_link_counts(session, project_id)
    orphan_evidence = sum(
        1
        for ev in evidence_repo.list_evidence(session, project_id)
        if link_counts.get(ev.id, 0) == 0
    )

    req_total = req_counts.total
    covered_pct = round(100 * req_counts.covered / req_total, 1) if req_total else 0.0

    return DashboardRead(
        requirements=req_counts,
        verification_items=vp_counts,
        requirement_total=req_total,
        covered_pct=covered_pct,
        suspect_links=suspect_links,
        orphan_requirements=orphan_reqs,
        orphan_verification_items=orphan_vps,
        orphan_evidence=orphan_evidence,
        latest_run=regression_service.latest_run_summary(session, project_id),
    )
