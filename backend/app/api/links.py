"""Link create / delete / clear-suspect endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.core.deps import CurrentUser, SessionDep
from app.schemas.link import LinkCreate, LinkCreated
from app.services import link_service
from app.services.item_service import DomainError

router = APIRouter(prefix="/links", tags=["links"])


@router.post("", response_model=LinkCreated, status_code=201)
def create_link(payload: LinkCreate, session: SessionDep, user: CurrentUser) -> LinkCreated:
    try:
        return link_service.create_link(session, payload, author=user)
    except DomainError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/{link_id}", status_code=204)
def delete_link(link_id: uuid.UUID, session: SessionDep, user: CurrentUser) -> None:
    try:
        link_service.delete_link(session, link_id, author=user)
    except DomainError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{link_id}/clear-suspect", response_model=LinkCreated)
def clear_suspect(link_id: uuid.UUID, session: SessionDep, user: CurrentUser) -> LinkCreated:
    try:
        return link_service.clear_suspect(session, link_id, author=user)
    except DomainError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
