"""API tests for the review workflow and comments."""

from __future__ import annotations

from app.models import Item, ItemRevision, ItemType, Project
from app.models.enums import ItemBaseKind, ProjectKind
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _requirement(db: Session) -> Item:
    project = Project(key="pcie", name="PCIe", kind=ProjectKind.IP)
    req_type = ItemType(
        project=project,
        key="requirement",
        name="Req",
        base_kind=ItemBaseKind.REQUIREMENT,
        id_prefix="REQ",
    )
    db.add_all([project, req_type])
    db.flush()
    item = Item(project=project, item_type=req_type, human_id="REQ-PCIE-001", seq=1)
    db.add(item)
    db.flush()
    rev = ItemRevision(item_id=item.id, rev_number=1, title="X", body="The X shall Y.", author="t")
    db.add(rev)
    db.flush()
    item.current_revision_id = rev.id
    db.flush()
    return item


def test_review_approve_flow(client: TestClient, db: Session) -> None:
    item = _requirement(db)

    resp = client.post(
        f"/api/items/{item.id}/reviews",
        json={"reviewers": [{"reviewer": "Clara Martin", "role": "Verification"}]},
    )
    assert resp.status_code == 201, resp.text
    detail = resp.json()
    assert detail["workflow_status"] == "in_review"
    assert detail["review"]["status"] == "in_review"
    review_id = detail["review"]["id"]

    # A comment shows up in the item's discussion.
    resp = client.post(f"/api/items/{item.id}/comments", json={"body": "Looks good to me."})
    assert resp.status_code == 201
    assert resp.json()["comments"][0]["body"] == "Looks good to me."

    # Approving the only reviewer approves the item.
    resp = client.post(
        f"/api/reviews/{review_id}/decision",
        json={"decision": "approved", "reviewer": "Clara Martin"},
    )
    assert resp.status_code == 200, resp.text
    detail = resp.json()
    assert detail["review"]["status"] == "approved"
    assert detail["workflow_status"] == "approved"


def test_review_request_changes_sends_back_to_draft(client: TestClient, db: Session) -> None:
    item = _requirement(db)
    review_id = client.post(
        f"/api/items/{item.id}/reviews", json={"reviewers": [{"reviewer": "A"}]}
    ).json()["review"]["id"]

    detail = client.post(
        f"/api/reviews/{review_id}/decision",
        json={"decision": "changes_requested", "reviewer": "A"},
    ).json()
    assert detail["review"]["status"] == "changes_requested"
    assert detail["workflow_status"] == "draft"
