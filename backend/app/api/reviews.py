"""Review decision endpoint."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.core.deps import CurrentUser, SessionDep
from app.schemas.item import ItemDetail
from app.schemas.review import ReviewDecisionIn
from app.services import item_service, review_service
from app.services.item_service import DomainError

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/{review_id}/decision", response_model=ItemDetail)
def decide(
    review_id: uuid.UUID, payload: ReviewDecisionIn, session: SessionDep, user: CurrentUser
) -> ItemDetail:
    try:
        review = review_service.decide(
            session, review_id, payload.decision, reviewer=payload.reviewer or user
        )
    except DomainError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    session.flush()
    detail = item_service.get_item_read(session, review.item_id)
    assert detail is not None
    return detail
