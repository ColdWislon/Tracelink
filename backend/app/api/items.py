"""Item create / read / update endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.core.deps import CurrentUser, SessionDep
from app.schemas.item import ItemCreate, ItemDetail, ItemRead, ItemUpdate
from app.services import item_service
from app.services.item_service import DomainError

router = APIRouter(prefix="/items", tags=["items"])


@router.post("", response_model=ItemDetail, status_code=201)
def create_item(payload: ItemCreate, session: SessionDep, user: CurrentUser) -> ItemDetail:
    try:
        item = item_service.create_item(session, payload, author=user)
    except DomainError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    session.flush()
    detail = item_service.get_item_read(session, item.id)
    assert detail is not None
    return detail


@router.get("/{item_id}", response_model=ItemDetail)
def get_item(item_id: uuid.UUID, session: SessionDep) -> ItemDetail:
    detail = item_service.get_item_read(session, item_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="item not found")
    return detail


@router.patch("/{item_id}", response_model=ItemDetail)
def update_item(
    item_id: uuid.UUID, payload: ItemUpdate, session: SessionDep, user: CurrentUser
) -> ItemDetail:
    try:
        item_service.update_item(session, item_id, payload, author=user)
    except DomainError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    session.flush()
    detail = item_service.get_item_read(session, item_id)
    assert detail is not None
    return detail


# Convenience: the item read model exposes both the grid and document view fields.
__all__ = ["router", "ItemRead"]
