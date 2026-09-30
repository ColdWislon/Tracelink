"""API tests for link create / clear-suspect / delete and suspect detection."""

from __future__ import annotations

from app.models import Evidence, Item, ItemRevision, ItemType, Project
from app.models.enums import EvidenceKind, ItemBaseKind, ProjectKind
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _item(db: Session, project: Project, itype: ItemType, human_id: str, seq: int) -> Item:
    item = Item(project=project, item_type=itype, human_id=human_id, seq=seq)
    db.add(item)
    db.flush()
    rev = ItemRevision(item_id=item.id, rev_number=1, title=human_id, body="orig", author="t")
    db.add(rev)
    db.flush()
    item.current_revision_id = rev.id
    db.flush()
    return item


def _setup(db: Session) -> tuple[Item, Item, Evidence]:
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
    ev = Evidence(project_id=project.id, kind=EvidenceKind.TEST, fqn="pcie_test", name="pcie_test")
    db.add(ev)
    db.flush()
    return req, vp, ev


def test_link_lifecycle(client: TestClient, db: Session) -> None:
    req, vp, ev = _setup(db)

    # verified_by: requirement -> verification item.
    resp = client.post(
        "/api/links",
        json={
            "link_type": "verified_by",
            "upstream_item_id": str(req.id),
            "downstream_item_id": str(vp.id),
        },
    )
    assert resp.status_code == 201, resp.text
    link = resp.json()
    assert link["suspect"] is False
    link_id = link["link_id"]

    # Idempotent: linking the same pair returns the same link.
    resp = client.post(
        "/api/links",
        json={
            "link_type": "verified_by",
            "upstream_item_id": str(req.id),
            "downstream_item_id": str(vp.id),
        },
    )
    assert resp.json()["link_id"] == link_id

    # evidenced_by: verification item -> evidence.
    resp = client.post(
        "/api/links",
        json={
            "link_type": "evidenced_by",
            "upstream_item_id": str(vp.id),
            "downstream_evidence_id": str(ev.id),
        },
    )
    assert resp.status_code == 201
    assert resp.json()["suspect"] is False

    # Changing the requirement makes the verified_by link suspect.
    client.patch(f"/api/items/{req.id}", json={"body": "The controller shall do X differently."})
    detail = client.get(f"/api/items/{req.id}").json()
    suspect_targets = {d["human_id"]: d["suspect"] for d in detail["downstream"]}
    assert suspect_targets["VP-PCIE-001"] is True

    # Clear suspect re-pins to the current revision.
    resp = client.post(f"/api/links/{link_id}/clear-suspect")
    assert resp.status_code == 200
    assert resp.json()["suspect"] is False
    detail = client.get(f"/api/items/{req.id}").json()
    assert {d["human_id"]: d["suspect"] for d in detail["downstream"]}["VP-PCIE-001"] is False

    # Delete removes it.
    assert client.delete(f"/api/links/{link_id}").status_code == 204
    detail = client.get(f"/api/items/{req.id}").json()
    assert all(d["human_id"] != "VP-PCIE-001" for d in detail["downstream"])


def test_link_rejects_self_and_bad_payload(client: TestClient, db: Session) -> None:
    req, _vp, _ev = _setup(db)
    # Two downstream targets at once.
    resp = client.post(
        "/api/links",
        json={
            "link_type": "verified_by",
            "upstream_item_id": str(req.id),
            "downstream_item_id": str(req.id),
            "downstream_evidence_id": str(_ev.id),
        },
    )
    assert resp.status_code == 422
