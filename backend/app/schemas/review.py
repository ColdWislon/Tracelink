"""Schemas for reviews, reviewer assignments, and comments."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ReviewDecision, ReviewStatus


class ReviewerIn(BaseModel):
    reviewer: str
    role: str | None = None


class ReviewRequest(BaseModel):
    reviewers: list[ReviewerIn] = []


class ReviewDecisionIn(BaseModel):
    decision: ReviewDecision
    reviewer: str | None = None


class CommentCreate(BaseModel):
    body: str


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    author: str
    body: str
    created_at: datetime


class ReviewAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reviewer: str
    role: str | None
    decision: ReviewDecision
    decided_at: datetime | None


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item_id: uuid.UUID
    revision_id: uuid.UUID | None
    status: ReviewStatus
    requested_by: str | None
    created_at: datetime
    assignments: list[ReviewAssignmentRead] = []
