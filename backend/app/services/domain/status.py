"""Pure status computation for verification items and requirement roll-up.

Default rule (configurable via :class:`StatusPolicy`):

* A verification item is **covered** when every piece of linked evidence ran and
  is satisfied — all tests passed, all coverpoints reached their goal, and all
  assertions fired with zero failures.
* **failing** when any evidence that ran reported an outright failure (a failed
  test count or a failed assertion). Coverpoints cannot fail, only under-reach.
* **not_run** when evidence exists but none of it ran.
* **partial** when some but not all evidence is satisfied.
* **uncovered** when there is no evidence at all.

A requirement rolls up from its verification items (all required by default).

No DB or I/O here; inputs are plain values so the logic is trivially testable.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import EvidenceKind, VerificationStatus


@dataclass(frozen=True)
class EvidenceOutcome:
    """Normalized metrics for one evidence result (mirrors EvidenceResult columns)."""

    kind: EvidenceKind
    passed: int | None = None
    failed: int | None = None
    total: int | None = None
    hits: int | None = None
    goal: int | None = None
    fired: int | None = None


@dataclass(frozen=True)
class EvidenceState:
    ran: bool
    satisfied: bool
    failing: bool


@dataclass(frozen=True)
class StatusPolicy:
    """Configurable knobs for status computation.

    ``require_all`` (default) means every verification item is required for a
    requirement to be covered. Weighting is a future extension.
    """

    require_all: bool = True


DEFAULT_POLICY = StatusPolicy()


def _i(value: int | None) -> int:
    return value or 0


def evidence_state(outcome: EvidenceOutcome) -> EvidenceState:
    """Derive (ran, satisfied, failing) for a single evidence result."""
    match outcome.kind:
        case EvidenceKind.TEST:
            executed = _i(outcome.passed) + _i(outcome.failed)
            ran = executed > 0
            failing = _i(outcome.failed) > 0
            satisfied = (
                ran
                and not failing
                and _i(outcome.total) > 0
                and _i(outcome.passed) >= _i(outcome.total)
            )
            return EvidenceState(ran=ran, satisfied=satisfied, failing=failing)
        case EvidenceKind.COVERPOINT:
            ran = _i(outcome.hits) > 0
            satisfied = ran and _i(outcome.hits) >= _i(outcome.goal)
            return EvidenceState(ran=ran, satisfied=satisfied, failing=False)
        case EvidenceKind.ASSERTION:
            ran = _i(outcome.fired) > 0
            failing = _i(outcome.failed) > 0
            satisfied = ran and not failing
            return EvidenceState(ran=ran, satisfied=satisfied, failing=failing)


def verification_item_status(
    states: list[EvidenceState], policy: StatusPolicy = DEFAULT_POLICY
) -> VerificationStatus:
    """Compute a verification item's status from its evidence states."""
    if not states:
        return VerificationStatus.UNCOVERED
    if any(s.failing for s in states):
        return VerificationStatus.FAILING
    if not any(s.ran for s in states):
        return VerificationStatus.NOT_RUN
    all_satisfied = all(s.ran and s.satisfied for s in states)
    if all_satisfied:
        return VerificationStatus.COVERED
    return VerificationStatus.PARTIAL


def rollup_requirement_status(
    vp_statuses: list[VerificationStatus], policy: StatusPolicy = DEFAULT_POLICY
) -> VerificationStatus:
    """Roll a requirement's status up from its verification items' statuses."""
    if not vp_statuses:
        return VerificationStatus.UNCOVERED
    statuses = set(vp_statuses)
    if VerificationStatus.FAILING in statuses:
        return VerificationStatus.FAILING
    if statuses == {VerificationStatus.COVERED}:
        return VerificationStatus.COVERED
    if statuses <= {VerificationStatus.NOT_RUN, VerificationStatus.UNCOVERED}:
        if VerificationStatus.NOT_RUN in statuses:
            return VerificationStatus.NOT_RUN
        return VerificationStatus.UNCOVERED
    return VerificationStatus.PARTIAL
