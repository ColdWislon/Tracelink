"""EARS checker tests, including the exact statements flagged in the design comp."""

from __future__ import annotations

from app.services.domain.ears import (
    EVENT_DRIVEN,
    STATE_DRIVEN,
    UBIQUITOUS,
    UNWANTED,
    check_ears,
    detect_pattern,
)


def test_pattern_detection() -> None:
    assert detect_pattern("When X, the controller shall Y.") == EVENT_DRIVEN
    assert detect_pattern("While in Recovery, the controller shall Y.") == STATE_DRIVEN
    assert (
        detect_pattern("Where MSI-X is enabled, the controller shall forward.")
        == "Optional feature"
    )
    assert detect_pattern("If a fetch returns SLVERR, then the engine shall abort.") == UNWANTED
    assert detect_pattern("The controller shall support 512-byte payloads.") == UBIQUITOUS
    assert detect_pattern("The controller handles timeouts.") is None


def test_clean_ubiquitous_requirement_has_no_errors() -> None:
    report = check_ears("The PCIe controller shall support a Max_Payload_Size of 512 bytes.")
    assert report.pattern == UBIQUITOUS
    assert report.ok
    assert [f for f in report.findings if f.severity == "error"] == []


def test_ambiguous_fast_is_flagged() -> None:
    # REQ-PCIE-018 in the comp: "... shall enter the L1 link state fast."
    text = "While the link is idle, the PCIe controller shall enter the L1 link state fast."
    report = check_ears(text)
    assert report.pattern == STATE_DRIVEN
    amb = [f for f in report.findings if f.code.startswith("QC-AMB")]
    assert len(amb) == 1
    # The span must cover the word "fast" so the editor can underline it.
    assert text[amb[0].start : amb[0].end] == "fast"
    assert amb[0].severity == "warning"


def test_missing_shall_and_untestable() -> None:
    # REQ-PCIE-020 in the comp: "The controller should handle completion timeouts gracefully."
    text = "The controller should handle completion timeouts gracefully."
    report = check_ears(text)
    assert report.pattern is None
    codes = {f.code for f in report.findings}
    assert "QC-SHL-01" in codes  # missing "shall"
    assert any(c.startswith("QC-TST") for c in codes)  # "gracefully" untestable

    shall = next(f for f in report.findings if f.code == "QC-SHL-01")
    assert text[shall.start : shall.end] == "should"

    tst = next(f for f in report.findings if f.code.startswith("QC-TST"))
    assert text[tst.start : tst.end] == "gracefully"
    assert tst.severity == "error"


def test_findings_sorted_by_position() -> None:
    report = check_ears("The system should do things quickly and gracefully.")
    positions = [f.start for f in report.findings]
    assert positions == sorted(positions)
