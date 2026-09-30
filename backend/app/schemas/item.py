"""Schemas for items, revisions, and their links."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    EvidenceKind,
    ItemBaseKind,
    LinkType,
    VerificationStatus,
    WorkflowStatus,
)


class LinkRef(BaseModel):
    """A resolved link endpoint as seen from one item."""

    link_id: uuid.UUID
    link_type: LinkType
    target: Literal["item", "evidence"]
    id: uuid.UUID
    human_id: str
    title: str
    suspect: bool = False
    base_kind: ItemBaseKind | None = None
    evidence_kind: EvidenceKind | None = None
    status: VerificationStatus | None = None


class RevisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rev_number: int
    title: str
    body: str
    attributes: dict[str, Any]
    ears_pattern: str | None
    author: str
    message: str | None
    created_at: datetime


class ItemRead(BaseModel):
    id: uuid.UUID
    human_id: str
    project_id: uuid.UUID
    project_key: str
    item_type_id: uuid.UUID
    type_key: str
    base_kind: ItemBaseKind
    title: str
    body: str
    attributes: dict[str, Any]
    ears_pattern: str | None
    workflow_status: WorkflowStatus
    applicability: str | None
    rev_number: int
    current_revision_id: uuid.UUID | None
    status: VerificationStatus | None = None
    upstream: list[LinkRef] = []
    downstream: list[LinkRef] = []


class ItemCreate(BaseModel):
    project_id: uuid.UUID
    item_type_id: uuid.UUID
    title: str = Field(min_length=1, max_length=500)
    body: str = ""
    attributes: dict[str, Any] = {}
    applicability: str | None = None
    workflow_status: WorkflowStatus = WorkflowStatus.DRAFT
    message: str | None = None


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    body: str | None = None
    attributes: dict[str, Any] | None = None
    applicability: str | None = None
    workflow_status: WorkflowStatus | None = None
    message: str | None = None


class ItemDetail(ItemRead):
    revisions: list[RevisionRead] = []
