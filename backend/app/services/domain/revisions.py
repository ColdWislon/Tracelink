"""Pure helpers for immutable revisions: numbering, change detection, diffing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def next_rev_number(current_max: int | None) -> int:
    """Return the next revision number (revisions start at 1)."""
    return (current_max or 0) + 1


def content_changed(
    old_title: str,
    old_body: str,
    old_attributes: dict[str, Any],
    new_title: str,
    new_body: str,
    new_attributes: dict[str, Any],
) -> bool:
    """True when any versioned content differs (a new revision is warranted)."""
    return old_title != new_title or old_body != new_body or old_attributes != new_attributes


@dataclass(frozen=True)
class TextDiff:
    """A single-span diff: shared ``pre``/``post`` around a changed middle."""

    pre: str
    deleted: str
    inserted: str
    post: str

    @property
    def changed(self) -> bool:
        return bool(self.deleted or self.inserted)


def diff_text(old: str, new: str) -> TextDiff:
    """Compute a minimal common-prefix/suffix diff (matches the UI's diff rendering)."""
    prefix_len = 0
    max_prefix = min(len(old), len(new))
    while prefix_len < max_prefix and old[prefix_len] == new[prefix_len]:
        prefix_len += 1

    suffix_len = 0
    max_suffix = min(len(old) - prefix_len, len(new) - prefix_len)
    while suffix_len < max_suffix and old[-1 - suffix_len] == new[-1 - suffix_len]:
        suffix_len += 1

    old_end = len(old) - suffix_len
    new_end = len(new) - suffix_len
    return TextDiff(
        pre=old[:prefix_len],
        deleted=old[prefix_len:old_end],
        inserted=new[prefix_len:new_end],
        post=old[old_end:] if suffix_len else "",
    )
