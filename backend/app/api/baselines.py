"""Baseline detail endpoint."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.core.deps import SessionDep
from app.schemas.baseline import BaselineDetail
from app.services import baseline_service

router = APIRouter(prefix="/baselines", tags=["baselines"])


@router.get("/{baseline_id}", response_model=BaselineDetail)
def get_baseline(baseline_id: uuid.UUID, session: SessionDep) -> BaselineDetail:
    detail = baseline_service.get_baseline_detail(session, baseline_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="baseline not found")
    return detail
