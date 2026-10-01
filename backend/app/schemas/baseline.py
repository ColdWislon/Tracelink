"""Schemas for baselines."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BaselineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    milestone: str | None = None
    description: str | None = None


class BaselineRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    milestone: str | None
    description: str | None
    frozen: bool
    created_by: str | None
    created_at: datetime
    entry_count: int


class BaselineEntryRead(BaseModel):
    item_id: uuid.UUID
    human_id: str
    title: str
    rev_number: int


class BaselineDetail(BaselineRead):
    entries: list[BaselineEntryRead] = []
