"""Rule-based EARS quality checker for requirement statements.

Detects the EARS pattern (Ubiquitous / Event-driven / State-driven /
Optional feature / Unwanted behaviour) and reports quality findings with
character spans so the editor can underline the offending text:

* ``QC-SHL-01`` — missing binding "shall".
* ``QC-EARS-01`` — no recognizable EARS pattern.
* ``QC-AMB-*``  — ambiguous term (no measurable bound).
* ``QC-TST-*``  — untestable wording (no pass/fail criterion).

Pure logic — no DB, no I/O.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# EARS pattern labels (match the design comp vocabulary).
UBIQUITOUS = "Ubiquitous"
EVENT_DRIVEN = "Event-driven"
STATE_DRIVEN = "State-driven"
OPTIONAL_FEATURE = "Optional feature"
UNWANTED = "Unwanted behaviour"

# Terms with no measurable bound.
AMBIGUOUS_TERMS = (
    "fast",
    "quickly",
    "rapidly",
    "slow",
    "slowly",
    "soon",
    "efficient",
    "efficiently",
    "minimal",
    "optimal",
    "reasonable",
    "reasonably",
    "sufficient",
    "sufficiently",
    "adequate",
    "adequately",
    "approximately",
    "several",
    "some",
    "many",
    "fast enough",
)

# Terms that give no pass/fail criterion.
UNTESTABLE_TERMS = (
    "gracefully",
    "properly",
    "correctly",
    "appropriately",
    "as appropriate",
    "as needed",
    "as required",
    "if necessary",
    "robustly",
    "seamlessly",
    "user-friendly",
    "etc",
)

# Non-binding modal verbs (a requirement should use "shall").
NON_BINDING = ("should", "must", "will", "may", "can", "could", "would")

_WORD = r"(?<!\w){term}(?!\w)"


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    severity: str  # "error" | "warning"
    start: int
    end: int
    term: str | None = None


@dataclass(frozen=True)
class EarsReport:
    pattern: str | None
    findings: list[Finding]

    @property
    def ok(self) -> bool:
        return self.pattern is not None and not any(f.severity == "error" for f in self.findings)


def _has_word(text: str, word: str) -> bool:
    return re.search(_WORD.format(term=re.escape(word)), text, re.IGNORECASE) is not None


def detect_pattern(text: str) -> str | None:
    """Return the EARS pattern label, or ``None`` if none is recognizable."""
    if not _has_word(text, "shall"):
        return None
    stripped = text.lstrip()
    lead = stripped.lower()
    if lead.startswith("when "):
        return EVENT_DRIVEN
    if lead.startswith("while "):
        return STATE_DRIVEN
    if lead.startswith("where "):
        return OPTIONAL_FEATURE
    if lead.startswith("if "):
        return UNWANTED
    return UBIQUITOUS


def _find_terms(
    text: str, terms: tuple[str, ...], code_prefix: str, severity: str, message_fmt: str
) -> list[Finding]:
    findings: list[Finding] = []
    for index, term in enumerate(terms, start=1):
        for match in re.finditer(_WORD.format(term=re.escape(term)), text, re.IGNORECASE):
            findings.append(
                Finding(
                    code=f"{code_prefix}-{index:02d}",
                    message=message_fmt.format(term=match.group(0)),
                    severity=severity,
                    start=match.start(),
                    end=match.end(),
                    term=match.group(0),
                )
            )
    return findings


def check_ears(text: str) -> EarsReport:
    """Analyze a requirement statement and return its pattern and findings."""
    findings: list[Finding] = []
    pattern = detect_pattern(text)

    has_shall = _has_word(text, "shall")
    if not has_shall:
        # Point at the first non-binding modal if present, else the whole text.
        span_start, span_end, term = 0, len(text), None
        for word in NON_BINDING:
            match = re.search(_WORD.format(term=re.escape(word)), text, re.IGNORECASE)
            if match:
                span_start, span_end, term = match.start(), match.end(), match.group(0)
                break
        detail = f'"{term}" is not binding' if term else "no binding verb"
        findings.append(
            Finding(
                code="QC-SHL-01",
                message=f'Missing "shall" — {detail} for a requirement.',
                severity="error",
                start=span_start,
                end=span_end,
                term=term,
            )
        )

    if pattern is None:
        findings.append(
            Finding(
                code="QC-EARS-01",
                message="No recognizable EARS pattern.",
                severity="warning",
                start=0,
                end=len(text),
            )
        )

    findings += _find_terms(
        text,
        UNTESTABLE_TERMS,
        "QC-TST",
        "error",
        'Not testable — "{term}" gives no pass/fail criterion.',
    )
    findings += _find_terms(
        text,
        AMBIGUOUS_TERMS,
        "QC-AMB",
        "warning",
        'Ambiguous term — "{term}" has no measurable bound.',
    )

    findings.sort(key=lambda f: (f.start, f.code))
    return EarsReport(pattern=pattern, findings=findings)
