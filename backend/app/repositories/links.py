"""Queries for individual links."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Link
from app.models.enums import LinkType


def get_link(session: Session, link_id: uuid.UUID) -> Link | None:
    return session.get(Link, link_id)


def find_link(
    session: Session,
    link_type: LinkType,
    upstream_item_id: uuid.UUID,
    downstream_item_id: uuid.UUID | None,
    downstream_evidence_id: uuid.UUID | None,
) -> Link | None:
    stmt = select(Link).where(
        Link.link_type == link_type,
        Link.upstream_item_id == upstream_item_id,
        Link.downstream_item_id == downstream_item_id,
        Link.downstream_evidence_id == downstream_evidence_id,
    )
    return session.execute(stmt).scalar_one_or_none()
