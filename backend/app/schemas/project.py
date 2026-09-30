"""Schemas for projects, variants, and item types."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import ItemBaseKind, ProjectKind


class VariantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    name: str
    description: str | None = None


class ItemTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID | None
    key: str
    name: str
    base_kind: ItemBaseKind
    id_prefix: str
    attribute_schema: list[dict[str, Any]]


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    name: str
    kind: ProjectKind
    parent_id: uuid.UUID | None
    is_ip_library: bool
    description: str | None = None
    variants: list[VariantRead] = []


class ProjectNode(ProjectRead):
    """A project with its children, for the hierarchy sidebar."""

    children: list[ProjectNode] = []
    item_count: int = 0
