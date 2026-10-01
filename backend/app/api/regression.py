"""Regression ingestion endpoint + its JSON Schema (Phase 3 pipeline entrypoint)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.deps import SessionDep
from app.schemas.evidence import RegressionRunAccepted, RegressionRunIn, RegressionRunRead
from app.services import regression_service
from app.services.item_service import DomainError

router = APIRouter(prefix="/regression", tags=["regression"])


@router.post("/runs", response_model=RegressionRunAccepted, status_code=201)
def ingest_run(payload: RegressionRunIn, session: SessionDep) -> RegressionRunAccepted:
    try:
        return regression_service.ingest_run(session, payload)
    except DomainError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/runs/{run_id}", response_model=RegressionRunRead)
def get_run(run_id: uuid.UUID, session: SessionDep) -> RegressionRunRead:
    run = regression_service.get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return run


@router.get("/schema")
def payload_schema() -> dict[str, Any]:
    """JSON Schema for the ingestion payload (documents the rtrack-push contract)."""
    return RegressionRunIn.model_json_schema()
