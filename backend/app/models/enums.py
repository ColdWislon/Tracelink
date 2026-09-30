"""Domain enumerations shared by models, schemas, and pure domain logic.

Values are stored as strings (``native_enum=False``) so migrations stay simple
and the vocabulary can evolve without Postgres ENUM juggling.
"""

from __future__ import annotations

import enum


class ProjectKind(enum.StrEnum):
    SOC = "soc"
    SUBSYSTEM = "subsystem"
    IP = "ip"


class ItemBaseKind(enum.StrEnum):
    """How the application treats an item type (extensible via ``OTHER``)."""

    REQUIREMENT = "requirement"
    VERIFICATION_ITEM = "verification_item"
    OTHER = "other"


class WorkflowStatus(enum.StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"


class LinkType(enum.StrEnum):
    DERIVES_FROM = "derives_from"
    VERIFIED_BY = "verified_by"
    EVIDENCED_BY = "evidenced_by"


class EvidenceKind(enum.StrEnum):
    TEST = "test"
    COVERPOINT = "coverpoint"
    ASSERTION = "assertion"


class VerificationStatus(enum.StrEnum):
    """Computed coverage status for a verification item, rolled up to requirements."""

    COVERED = "covered"
    PARTIAL = "partial"
    FAILING = "failing"
    NOT_RUN = "not_run"
    UNCOVERED = "uncovered"


class ReviewStatus(enum.StrEnum):
    REQUESTED = "requested"
    IN_REVIEW = "in_review"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"


class ReviewDecision(enum.StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
