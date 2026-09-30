"""Pure suspect-link logic.

A link is *suspect* when the upstream item's current revision differs from the
revision the link was last reviewed against. Evidence links (which have no
reviewed revision) are never suspect.
"""

from __future__ import annotations

import uuid


def link_is_suspect(
    upstream_current_revision_id: uuid.UUID | None,
    reviewed_upstream_revision_id: uuid.UUID | None,
) -> bool:
    """True when the reviewed baseline no longer matches the upstream's current revision."""
    if reviewed_upstream_revision_id is None:
        return False
    return upstream_current_revision_id != reviewed_upstream_revision_id
