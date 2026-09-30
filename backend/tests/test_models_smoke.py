"""ORM smoke test: exercise the core model wiring against the database.

Chiefly validates the deferred self-referential FK
(``item.current_revision_id -> item_revision.id``) and the JSONB attribute column.
"""

from __future__ import annotations

from app.models import Item, ItemRevision, ItemType, Project
from app.models.enums import ItemBaseKind, ProjectKind, WorkflowStatus
from sqlalchemy import select
from sqlalchemy.orm import Session


def test_create_item_with_revision(db: Session) -> None:
    project = Project(key="pcie", name="PCIe Gen4 Controller", kind=ProjectKind.IP)
    item_type = ItemType(
        project=project,
        key="requirement",
        name="Requirement",
        base_kind=ItemBaseKind.REQUIREMENT,
        id_prefix="REQ",
        attribute_schema=[{"key": "priority", "label": "Priority", "type": "enum"}],
    )
    db.add_all([project, item_type])
    db.flush()

    item = Item(
        project=project,
        item_type=item_type,
        human_id="REQ-PCIE-001",
        seq=1,
        workflow_status=WorkflowStatus.APPROVED,
        applicability="A0",
    )
    db.add(item)
    db.flush()

    rev = ItemRevision(
        item=item,
        rev_number=1,
        title="Gen4 link training on x4",
        body="When both partners advertise 16.0 GT/s, the controller shall complete "
        "link training at Gen4 on 4 lanes.",
        attributes={"priority": "P1"},
        ears_pattern="Event-driven",
        author="A. Moreau",
    )
    db.add(rev)
    db.flush()

    # Point the item at its current revision (the deferred self-FK).
    item.current_revision_id = rev.id
    db.flush()

    loaded = db.execute(select(Item).where(Item.human_id == "REQ-PCIE-001")).scalar_one()
    assert loaded.current_revision is not None
    assert loaded.current_revision.title == "Gen4 link training on x4"
    assert loaded.current_revision.attributes["priority"] == "P1"
    assert loaded.workflow_status is WorkflowStatus.APPROVED
    assert len(loaded.revisions) == 1
