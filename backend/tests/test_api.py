"""API tests for item CRUD, revisions, EARS, project tree, and ingestion."""

from __future__ import annotations

from app.models import ItemType, Project
from app.models.enums import ItemBaseKind, ProjectKind
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

REQ_SCHEMA = [
    {
        "key": "priority",
        "type": "enum",
        "options": ["P1", "P2", "P3"],
        "required": True,
        "default": "P2",
    }
]


def _make_project(db: Session, key: str = "pcie") -> tuple[Project, ItemType]:
    project = Project(key=key, name="PCIe Gen4 Controller", kind=ProjectKind.IP)
    req_type = ItemType(
        project=project,
        key="requirement",
        name="Requirement",
        base_kind=ItemBaseKind.REQUIREMENT,
        id_prefix="REQ",
        attribute_schema=REQ_SCHEMA,
    )
    db.add_all([project, req_type])
    db.flush()
    return project, req_type


def test_create_read_update_item(client: TestClient, db: Session) -> None:
    project, req_type = _make_project(db)

    resp = client.post(
        "/api/items",
        json={
            "project_id": str(project.id),
            "item_type_id": str(req_type.id),
            "title": "512-byte max payload size",
            "body": "The PCIe controller shall support a Max_Payload_Size of 512 bytes.",
            "attributes": {"priority": "P1"},
        },
    )
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["human_id"] == "REQ-PCIE-001"
    assert created["rev_number"] == 1
    assert created["ears_pattern"] == "Ubiquitous"
    assert created["status"] == "uncovered"  # no verification items linked
    item_id = created["id"]

    # Editing the body creates a new revision.
    resp = client.patch(
        f"/api/items/{item_id}",
        json={"body": "While the link is idle, the PCIe controller shall enter L1 within 2 us."},
    )
    assert resp.status_code == 200, resp.text
    updated = resp.json()
    assert updated["rev_number"] == 2
    assert updated["ears_pattern"] == "State-driven"

    resp = client.get(f"/api/items/{item_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert len(detail["revisions"]) == 2
    assert detail["revisions"][0]["rev_number"] == 2  # newest first


def test_create_item_rejects_bad_attribute(client: TestClient, db: Session) -> None:
    project, req_type = _make_project(db, key="dma")
    resp = client.post(
        "/api/items",
        json={
            "project_id": str(project.id),
            "item_type_id": str(req_type.id),
            "title": "X",
            "body": "The engine shall do X.",
            "attributes": {"priority": "P9"},
        },
    )
    assert resp.status_code == 422


def test_list_items_and_project_tree(client: TestClient, db: Session) -> None:
    project, req_type = _make_project(db, key="irq")
    client.post(
        "/api/items",
        json={
            "project_id": str(project.id),
            "item_type_id": str(req_type.id),
            "title": "256 sources",
            "body": "The interrupt controller shall accept 256 sources.",
            "attributes": {"priority": "P1"},
        },
    )
    items = client.get(f"/api/projects/{project.id}/items").json()
    assert len(items) == 1

    tree = client.get("/api/projects").json()
    assert any(node["key"] == "irq" and node["item_count"] == 1 for node in tree)


def test_ears_check_endpoint(client: TestClient) -> None:
    resp = client.post(
        "/api/ears/check",
        json={"text": "The controller should handle completion timeouts gracefully."},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["pattern"] is None
    codes = {f["code"] for f in body["findings"]}
    assert "QC-SHL-01" in codes


def test_regression_ingest(client: TestClient, db: Session) -> None:
    project, _ = _make_project(db, key="pcie")
    resp = client.post(
        "/api/regression/runs",
        json={
            "project_key": "pcie",
            "source": "jenkins",
            "external_id": "#1842",
            "results": [
                {"kind": "test", "fqn": "pcie_smoke_test", "passed": 10, "failed": 0, "total": 10},
                {"kind": "coverpoint", "fqn": "cg_x.cp_y", "hits": 100, "goal": 100},
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["result_count"] == 2
    assert body["created_evidence"] == 2


def test_regression_schema_endpoint(client: TestClient) -> None:
    schema = client.get("/api/regression/schema").json()
    assert schema["title"] == "RegressionRunIn"
    assert "results" in schema["properties"]
