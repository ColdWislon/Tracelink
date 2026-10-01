"""Review workflow orchestration: request a review, record decisions, comment."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import AuditLog, Comment, Review, ReviewAssignment
from app.models.enums import ReviewDecision, ReviewStatus, WorkflowStatus
from app.repositories import items as item_repo
from app.repositories import reviews as review_repo
from app.schemas.review import ReviewerIn
from app.services.item_service import DomainError


def _audit(
    session: Session, review_id: uuid.UUID, action: str, actor: str, **detail: object
) -> None:
    session.add(
        AuditLog(
            entity_type="review", entity_id=review_id, action=action, actor=actor, detail=detail
        )
    )


def request_review(
    session: Session, item_id: uuid.UUID, reviewers: list[ReviewerIn], author: str
) -> Review:
    item = item_repo.get_item(session, item_id)
    if item is None:
        raise DomainError("item not found")

    review = Review(
        item_id=item.id,
        revision_id=item.current_revision_id,
        status=ReviewStatus.IN_REVIEW,
        requested_by=author,
    )
    session.add(review)
    session.flush()

    chosen = reviewers or [ReviewerIn(reviewer=author)]
    for r in chosen:
        session.add(ReviewAssignment(review_id=review.id, reviewer=r.reviewer, role=r.role))
    item.workflow_status = WorkflowStatus.IN_REVIEW
    _audit(session, review.id, "request", author, reviewers=[r.reviewer for r in chosen])
    session.flush()
    return review


def decide(
    session: Session, review_id: uuid.UUID, decision: ReviewDecision, reviewer: str
) -> Review:
    review = review_repo.get_review(session, review_id)
    if review is None:
        raise DomainError("review not found")

    assignment = next((a for a in review.assignments if a.reviewer == reviewer), None)
    if assignment is None:
        assignment = ReviewAssignment(review_id=review.id, reviewer=reviewer)
        session.add(assignment)
        review.assignments.append(assignment)
    assignment.decision = decision
    assignment.decided_at = datetime.now(UTC)
    session.flush()

    item = item_repo.get_item(session, review.item_id)
    assert item is not None

    if any(a.decision is ReviewDecision.CHANGES_REQUESTED for a in review.assignments):
        review.status = ReviewStatus.CHANGES_REQUESTED
        item.workflow_status = WorkflowStatus.DRAFT
    elif all(a.decision is ReviewDecision.APPROVED for a in review.assignments):
        review.status = ReviewStatus.APPROVED
        item.workflow_status = WorkflowStatus.APPROVED
    else:
        review.status = ReviewStatus.IN_REVIEW

    _audit(session, review.id, "decision", reviewer, decision=decision.value)
    session.flush()
    return review


def add_comment(session: Session, item_id: uuid.UUID, body: str, author: str) -> Comment:
    item = item_repo.get_item(session, item_id)
    if item is None:
        raise DomainError("item not found")
    if not body.strip():
        raise DomainError("comment body is required")
    review = review_repo.latest_review_for_item(session, item_id)
    comment = Comment(
        item_id=item_id,
        review_id=review.id if review else None,
        body=body.strip(),
        author=author,
    )
    session.add(comment)
    session.flush()
    return comment
