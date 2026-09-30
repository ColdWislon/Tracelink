"""End-to-end status wiring: links + a regression run -> computed statuses."""

from __future__ import annotations

from datetime import UTC, datetime

from app.models import (
    Evidence,
    EvidenceResult,
    Item,
    ItemRevision,
    ItemType,
    Link,
    Project,
    RegressionRun,
)
from app.models.enums import (
    EvidenceKind,
    ItemBaseKind,
    LinkType,
    ProjectKind,
    VerificationStatus,
)
from app.services import status_service
from sqlalchemy.orm import Session


def _item(db: Session, project: Project, itype: ItemType, human_id: str, seq: int) -> Item:
    item = Item(project=project, item_type=itype, human_id=human_id, seq=seq)
    db.add(item)
    db.flush()
    rev = ItemRevision(item_id=item.id, rev_number=1, title=human_id, body="", author="t")
    db.add(rev)
    db.flush()
    item.current_revision_id = rev.id
    db.flush()
    return item


def test_status_pipeline(db: Session) -> None:
    project = Project(key="pcie", name="PCIe", kind=ProjectKind.IP)
    req_type = ItemType(
        project=project,
        key="requirement",
        name="Req",
        base_kind=ItemBaseKind.REQUIREMENT,
        id_prefix="REQ",
    )
    vp_type = ItemType(
        project=project,
        key="verification_item",
        name="VP",
        base_kind=ItemBaseKind.VERIFICATION_ITEM,
        id_prefix="VP",
    )
    db.add_all([project, req_type, vp_type])
    db.flush()

    req = _item(db, project, req_type, "REQ-PCIE-001", 1)
    vp = _item(db, project, vp_type, "VP-PCIE-001", 1)

    test_ev = Evidence(
        project_id=project.id, kind=EvidenceKind.TEST, fqn="pcie_test", name="pcie_test"
    )
    assert_ev = Evidence(project_id=project.id, kind=EvidenceKind.ASSERTION, fqn="a_x", name="a_x")
    db.add_all([test_ev, assert_ev])
    db.flush()

    db.add_all(
        [
            Link(link_type=LinkType.VERIFIED_BY, upstream_item_id=req.id, downstream_item_id=vp.id),
            Link(
                link_type=LinkType.EVIDENCED_BY,
                upstream_item_id=vp.id,
                downstream_evidence_id=test_ev.id,
            ),
            Link(
                link_type=LinkType.EVIDENCED_BY,
                upstream_item_id=vp.id,
                downstream_evidence_id=assert_ev.id,
            ),
        ]
    )

    run = RegressionRun(project_id=project.id, source="jenkins", imported_at=datetime.now(UTC))
    db.add(run)
    db.flush()
    db.add_all(
        [
            EvidenceResult(
                run_id=run.id,
                evidence_id=test_ev.id,
                kind=EvidenceKind.TEST,
                passed=10,
                failed=0,
                total=10,
            ),
            EvidenceResult(
                run_id=run.id,
                evidence_id=assert_ev.id,
                kind=EvidenceKind.ASSERTION,
                fired=500,
                failed=0,
            ),
        ]
    )
    db.flush()

    statuses = status_service.compute_statuses(db, project.id)
    assert statuses[vp.id] == VerificationStatus.COVERED
    assert statuses[req.id] == VerificationStatus.COVERED

    # A failing assertion flips the plan item and its requirement to failing.
    result = next(r for r in db.query(EvidenceResult).all() if r.evidence_id == assert_ev.id)
    result.failed = 3
    db.flush()
    statuses = status_service.compute_statuses(db, project.id)
    assert statuses[vp.id] == VerificationStatus.FAILING
    assert statuses[req.id] == VerificationStatus.FAILING
