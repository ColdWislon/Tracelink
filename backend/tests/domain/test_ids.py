from __future__ import annotations

import pytest
from app.services.domain.ids import format_human_id, next_sequence


def test_next_sequence() -> None:
    assert next_sequence(None) == 1
    assert next_sequence(0) == 1
    assert next_sequence(7) == 8


def test_format_human_id() -> None:
    assert format_human_id("REQ", "pcie", 1) == "REQ-PCIE-001"
    assert format_human_id("VP", "DMA", 24) == "VP-DMA-024"
    assert format_human_id("REQ", "irq", 100) == "REQ-IRQ-100"
    assert format_human_id("REQ", "pcie", 1234) == "REQ-PCIE-1234"


def test_format_human_id_rejects_bad_sequence() -> None:
    with pytest.raises(ValueError):
        format_human_id("REQ", "pcie", 0)
