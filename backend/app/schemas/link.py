"""Schemas for link create/read."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, model_validator

from app.models.enums import LinkType


class LinkCreate(BaseModel):
    link_type: LinkType
    upstream_item_id: uuid.UUID
    downstream_item_id: uuid.UUID | None = None
    downstream_evidence_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _exactly_one_downstream(self) -> LinkCreate:
        if (self.downstream_item_id is None) == (self.downstream_evidence_id is None):
            raise ValueError(
                "exactly one of downstream_item_id / downstream_evidence_id is required"
            )
        return self


class LinkCreated(BaseModel):
    link_id: uuid.UUID
    link_type: LinkType
    upstream_item_id: uuid.UUID
    downstream_item_id: uuid.UUID | None
    downstream_evidence_id: uuid.UUID | None
    suspect: bool
