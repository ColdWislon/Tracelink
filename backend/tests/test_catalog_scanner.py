"""Tests for the SystemVerilog catalog scanner against a small fixture."""

from __future__ import annotations

from pathlib import Path

from app.catalog import scan_repo, scan_text
from app.models.enums import EvidenceKind

FIXTURES = Path(__file__).parent / "fixtures" / "sv"


def _fqns(candidates: list, kind: EvidenceKind) -> set[str]:
    return {c.fqn for c in candidates if c.kind == kind}


def test_scan_text_extracts_evidence() -> None:
    candidates = scan_text((FIXTURES / "pcie_tests.sv").read_text())

    tests = _fqns(candidates, EvidenceKind.TEST)
    assert "pcie_gen4_linkup_test" in tests
    assert "pcie_mps_512_test" in tests
    assert "fake_should_not_match" not in tests  # inside a block comment

    coverpoints = _fqns(candidates, EvidenceKind.COVERPOINT)
    assert "cg_ltssm.cp_rate" in coverpoints
    assert "cg_ltssm.cp_width" in coverpoints
    assert "cg_ltssm.cx_rate_x_width" in coverpoints

    assertions = _fqns(candidates, EvidenceKind.ASSERTION)
    assert "a_ltssm_legal_trans" in assertions
    assert "a_ecrc_irq_latency" in assertions


def test_scan_repo_walks_directory() -> None:
    candidates = scan_repo(FIXTURES)
    assert any(c.kind == EvidenceKind.TEST for c in candidates)
    # meta records the source file relative path.
    assert all(c.meta.get("source") for c in candidates)
