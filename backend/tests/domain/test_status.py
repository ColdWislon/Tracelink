"""Status computation — validated against the exact evidence in the design comp."""

from __future__ import annotations

import pytest
from app.models.enums import EvidenceKind, VerificationStatus
from app.services.domain.status import (
    EvidenceOutcome,
    EvidenceState,
    evidence_state,
    rollup_requirement_status,
    verification_item_status,
)


def _test(passed: int, total: int, failed: int = 0) -> EvidenceOutcome:
    return EvidenceOutcome(EvidenceKind.TEST, passed=passed, total=total, failed=failed)


def _cp(hits: int, goal: int) -> EvidenceOutcome:
    return EvidenceOutcome(EvidenceKind.COVERPOINT, hits=hits, goal=goal)


def _assert(fired: int, failed: int) -> EvidenceOutcome:
    return EvidenceOutcome(EvidenceKind.ASSERTION, fired=fired, failed=failed)


def _status(*outcomes: EvidenceOutcome) -> VerificationStatus:
    return verification_item_status([evidence_state(o) for o in outcomes])


# --- single-result behavior -------------------------------------------------


def test_test_outcomes() -> None:
    assert evidence_state(_test(50, 50)) == EvidenceState(True, True, False)
    assert evidence_state(_test(18, 20)) == EvidenceState(True, False, False)
    assert evidence_state(_test(0, 0)) == EvidenceState(False, False, False)
    assert evidence_state(_test(10, 20, failed=5)) == EvidenceState(True, False, True)


def test_coverpoint_outcomes() -> None:
    assert evidence_state(_cp(100, 100)) == EvidenceState(True, True, False)
    assert evidence_state(_cp(71, 100)) == EvidenceState(True, False, False)
    assert evidence_state(_cp(0, 100)) == EvidenceState(False, False, False)


def test_assertion_outcomes() -> None:
    assert evidence_state(_assert(88120, 0)) == EvidenceState(True, True, False)
    assert evidence_state(_assert(20114, 3)) == EvidenceState(True, False, True)
    assert evidence_state(_assert(0, 0)) == EvidenceState(False, False, False)


def test_empty_evidence_is_uncovered() -> None:
    assert verification_item_status([]) == VerificationStatus.UNCOVERED


# --- verification item status, one case per seeded plan item ----------------

VP_CASES: dict[str, tuple[VerificationStatus, list[EvidenceOutcome]]] = {
    "VP-PCIE-001": (
        VerificationStatus.COVERED,
        [_test(50, 50), _cp(100, 100), _cp(100, 100), _assert(88120, 0)],
    ),
    "VP-PCIE-002": (VerificationStatus.COVERED, [_test(40, 40), _cp(100, 100)]),
    "VP-PCIE-005": (VerificationStatus.PARTIAL, [_test(30, 30), _cp(71, 100), _assert(3610, 0)]),
    "VP-PCIE-008": (VerificationStatus.COVERED, [_test(25, 25), _cp(100, 100)]),
    "VP-PCIE-016": (VerificationStatus.COVERED, [_test(20, 20), _cp(100, 100), _assert(602, 0)]),
    "VP-PCIE-019": (VerificationStatus.PARTIAL, [_test(18, 20), _cp(80, 100), _assert(955, 0)]),
    "VP-PCIE-021": (
        VerificationStatus.PARTIAL,
        [
            _test(48, 50),
            _test(12, 12),
            _cp(87, 100),
            _cp(72, 90),
            _assert(1204, 0),
            _assert(1198, 0),
        ],
    ),
    "VP-PCIE-022": (VerificationStatus.COVERED, [_test(20, 20), _cp(100, 100), _assert(1204, 0)]),
    "VP-PCIE-024": (VerificationStatus.NOT_RUN, [_test(0, 0), _cp(0, 100)]),
    "VP-DMA-001": (VerificationStatus.COVERED, [_test(30, 30), _cp(100, 100), _assert(12400, 0)]),
    "VP-DMA-002": (VerificationStatus.COVERED, [_test(60, 60), _cp(100, 100)]),
    "VP-DMA-004": (VerificationStatus.COVERED, [_test(40, 40), _cp(100, 100), _assert(5530, 0)]),
    "VP-DMA-005": (VerificationStatus.PARTIAL, [_test(9, 12), _cp(66, 100)]),
    "VP-DMA-007": (VerificationStatus.COVERED, [_test(30, 30), _cp(100, 100), _assert(2410, 0)]),
    "VP-DMA-010": (VerificationStatus.FAILING, [_test(14, 20), _cp(94, 100), _assert(20114, 3)]),
    "VP-IRQ-001": (VerificationStatus.COVERED, [_test(16, 16), _cp(100, 100)]),
    "VP-IRQ-003": (VerificationStatus.COVERED, [_test(24, 24), _cp(100, 100), _assert(7702, 0)]),
    "VP-IRQ-005": (VerificationStatus.COVERED, [_test(12, 12), _cp(100, 100)]),
    "VP-IRQ-008": (VerificationStatus.NOT_RUN, [_test(0, 0), _assert(0, 0)]),
    "VP-IRQ-012": (VerificationStatus.COVERED, [_test(10, 10)]),
}


@pytest.mark.parametrize("vp_id", list(VP_CASES))
def test_seeded_verification_item_status(vp_id: str) -> None:
    expected, outcomes = VP_CASES[vp_id]
    assert _status(*outcomes) == expected, vp_id


# --- requirement roll-up, one case per seeded requirement -------------------

S = VerificationStatus
REQ_CASES: dict[str, tuple[VerificationStatus, list[VerificationStatus]]] = {
    "REQ-PCIE-001": (S.COVERED, [S.COVERED, S.COVERED]),
    "REQ-PCIE-004": (S.PARTIAL, [S.PARTIAL]),
    "REQ-PCIE-007": (S.COVERED, [S.COVERED]),
    "REQ-PCIE-012": (S.PARTIAL, [S.PARTIAL, S.COVERED]),
    "REQ-PCIE-015": (S.COVERED, [S.COVERED]),
    "REQ-PCIE-018": (S.PARTIAL, [S.PARTIAL]),
    "REQ-PCIE-020": (S.NOT_RUN, [S.NOT_RUN]),
    "REQ-DMA-001": (S.COVERED, [S.COVERED, S.COVERED]),
    "REQ-DMA-003": (S.PARTIAL, [S.COVERED, S.PARTIAL]),
    "REQ-DMA-006": (S.COVERED, [S.COVERED]),
    "REQ-DMA-009": (S.FAILING, [S.FAILING]),
    "REQ-DMA-011": (S.UNCOVERED, []),
    "REQ-IRQ-001": (S.COVERED, [S.COVERED]),
    "REQ-IRQ-004": (S.COVERED, [S.COVERED, S.COVERED]),
    "REQ-IRQ-007": (S.NOT_RUN, [S.NOT_RUN]),
    "REQ-IRQ-009": (S.UNCOVERED, []),
}


@pytest.mark.parametrize("req_id", list(REQ_CASES))
def test_seeded_requirement_rollup(req_id: str) -> None:
    expected, vp_statuses = REQ_CASES[req_id]
    assert rollup_requirement_status(vp_statuses) == expected, req_id


def test_rollup_failing_dominates() -> None:
    assert rollup_requirement_status([S.COVERED, S.FAILING, S.NOT_RUN]) == S.FAILING


def test_rollup_mixed_notrun_uncovered() -> None:
    assert rollup_requirement_status([S.NOT_RUN, S.UNCOVERED]) == S.NOT_RUN
