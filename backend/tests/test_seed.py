"""Verify the seed reproduces the design comp: statuses, suspects, counts."""

from __future__ import annotations

import pytest
from app import seed as seed_module
from app.models import Item, Project
from app.models.enums import VerificationStatus
from app.repositories.projects import get_project_by_key
from app.services import item_service, status_service
from sqlalchemy import select
from sqlalchemy.orm import Session

# Expected coverage per requirement/plan item, straight from the comp.
EXPECTED_STATUS = {
    "REQ-PCIE-001": VerificationStatus.COVERED,
    "REQ-PCIE-004": VerificationStatus.PARTIAL,
    "REQ-PCIE-007": VerificationStatus.COVERED,
    "REQ-PCIE-012": VerificationStatus.PARTIAL,
    "REQ-PCIE-015": VerificationStatus.COVERED,
    "REQ-PCIE-018": VerificationStatus.PARTIAL,
    "REQ-PCIE-020": VerificationStatus.NOT_RUN,
    "REQ-DMA-001": VerificationStatus.COVERED,
    "REQ-DMA-003": VerificationStatus.PARTIAL,
    "REQ-DMA-006": VerificationStatus.COVERED,
    "REQ-DMA-009": VerificationStatus.FAILING,
    "REQ-DMA-011": VerificationStatus.UNCOVERED,
    "REQ-IRQ-001": VerificationStatus.COVERED,
    "REQ-IRQ-004": VerificationStatus.COVERED,
    "REQ-IRQ-007": VerificationStatus.NOT_RUN,
    "REQ-IRQ-009": VerificationStatus.UNCOVERED,
    "VP-DMA-010": VerificationStatus.FAILING,
    "VP-PCIE-024": VerificationStatus.NOT_RUN,
    "VP-IRQ-008": VerificationStatus.NOT_RUN,
}


@pytest.fixture
def seeded(db: Session) -> Session:
    seed_module.seed(db)
    return db


def test_counts(seeded: Session) -> None:
    reqs = seeded.execute(select(Item).where(Item.human_id.like("REQ-%"))).scalars().all()
    vps = seeded.execute(select(Item).where(Item.human_id.like("VP-%"))).scalars().all()
    assert len(reqs) == 16
    assert len(vps) == 20


def test_statuses_match_comp(seeded: Session) -> None:
    by_human = {i.human_id: i for i in seeded.execute(select(Item)).scalars().all()}
    # Statuses are computed per IP project; merge the three.
    statuses: dict[str, VerificationStatus] = {}
    for key in ("pcie", "dma", "irq"):
        project = get_project_by_key(seeded, key)
        assert project is not None
        computed = status_service.compute_statuses(seeded, project.id)
        for item_id, status in computed.items():
            statuses[next(h for h, i in by_human.items() if i.id == item_id)] = status

    for human_id, expected in EXPECTED_STATUS.items():
        assert statuses[human_id] == expected, human_id


def test_suspect_links(seeded: Session) -> None:
    pcie = get_project_by_key(seeded, "pcie")
    assert pcie is not None
    reads = {r.human_id: r for r in item_service.list_item_reads(seeded, pcie.id)}

    req012 = reads["REQ-PCIE-012"]
    suspect_targets = {ref.human_id for ref in req012.downstream if ref.suspect}
    assert "VP-PCIE-021" in suspect_targets
    assert "VP-PCIE-022" not in suspect_targets  # reviewed against current revision


def test_orphan_evidence_present(seeded: Session) -> None:
    from app.repositories import evidence as evidence_repo

    pcie = get_project_by_key(seeded, "pcie")
    assert pcie is not None
    fqns = {e.fqn for e in evidence_repo.list_evidence(seeded, pcie.id)}
    assert "pcie_ltssm_recovery_test" in fqns  # catalog-only orphan
    assert "a_pcie_rx_credit_ovf" in fqns


def test_evidence_catalog_has_metrics(seeded: Session) -> None:
    from app.services import evidence_service

    pcie = get_project_by_key(seeded, "pcie")
    assert pcie is not None
    catalog = {e.fqn: e for e in evidence_service.list_catalog(seeded, pcie.id)}

    linkup = catalog["pcie_gen4_linkup_test"]
    assert (linkup.passed, linkup.total) == (50, 50)
    assert linkup.satisfied is True
    assert linkup.link_count >= 1

    orphan = catalog["pcie_ecrc_multi_tlp_test"]
    assert orphan.link_count == 0
    assert orphan.ran is False


def test_dashboard_and_runs(seeded: Session) -> None:
    from app.services import dashboard_service, regression_service

    pcie = get_project_by_key(seeded, "pcie")
    assert pcie is not None

    dash = dashboard_service.compute(seeded, pcie.id)
    # PCIe: 7 requirements, 3 covered in the comp.
    assert dash.requirements.total == 7
    assert dash.requirements.covered == 3
    assert dash.covered_pct == round(100 * 3 / 7, 1)
    assert dash.suspect_links >= 1  # REQ-PCIE-012 -> VP-PCIE-021
    assert dash.latest_run is not None
    assert dash.latest_run.external_id == "#1842"

    # Runs are recorded at the SoC level but visible from the IP via the hierarchy.
    runs = regression_service.list_runs(seeded, pcie.id)
    assert len(runs) == 1
    assert runs[0].tests.total > 0


def test_baseline_snapshots_subtree(seeded: Session) -> None:
    from app.schemas.baseline import BaselineCreate
    from app.services import baseline_service

    aurora = get_project_by_key(seeded, "aurora")
    assert aurora is not None
    detail = baseline_service.create_baseline(
        seeded, aurora.id, BaselineCreate(name="RTL freeze", milestone="RTL"), author="tester"
    )
    # A SoC baseline captures all 36 items across PCIe/DMA/IRQ (16 req + 20 vp).
    assert detail.entry_count == 36
    assert detail.frozen is True
    assert any(e.human_id == "REQ-PCIE-012" and e.rev_number == 4 for e in detail.entries)

    names = [b.name for b in baseline_service.list_baselines(seeded, aurora.id)]
    assert "RTL freeze" in names


def test_aurora_hierarchy(seeded: Session) -> None:
    aurora = get_project_by_key(seeded, "aurora")
    assert aurora is not None
    children = seeded.execute(select(Project).where(Project.parent_id == aurora.id)).scalars().all()
    assert {c.key for c in children} == {"pcie", "dma", "irq"}
