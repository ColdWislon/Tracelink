from __future__ import annotations

import uuid

from app.services.domain.links import link_is_suspect


def test_not_suspect_when_reviewed_matches_current() -> None:
    rev = uuid.uuid4()
    assert not link_is_suspect(rev, rev)


def test_suspect_when_upstream_advanced() -> None:
    reviewed = uuid.uuid4()
    current = uuid.uuid4()
    assert link_is_suspect(current, reviewed)


def test_evidence_link_never_suspect() -> None:
    # Evidence links carry no reviewed revision.
    assert not link_is_suspect(uuid.uuid4(), None)
