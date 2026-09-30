from __future__ import annotations

from app.services.domain.revisions import content_changed, diff_text, next_rev_number


def test_next_rev_number() -> None:
    assert next_rev_number(None) == 1
    assert next_rev_number(3) == 4


def test_content_changed() -> None:
    assert not content_changed("t", "b", {"a": 1}, "t", "b", {"a": 1})
    assert content_changed("t", "b", {"a": 1}, "t2", "b", {"a": 1})
    assert content_changed("t", "b", {"a": 1}, "t", "b", {"a": 2})


def test_diff_text_single_span() -> None:
    old = "enter the L1 link state fast."
    new = "enter the L1 link state within 2 us of the timer expiring."
    diff = diff_text(old, new)
    assert diff.pre == "enter the L1 link state "
    assert diff.deleted == "fast"
    assert diff.inserted == "within 2 us of the timer expiring"
    assert diff.post == "."
    assert diff.changed


def test_diff_text_no_change() -> None:
    diff = diff_text("same", "same")
    assert not diff.changed
    assert diff.pre == "same"
