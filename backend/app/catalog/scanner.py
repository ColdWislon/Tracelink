"""Extract an evidence catalog from a SystemVerilog testbench.

Finds ``uvm_test`` subclasses, covergroup coverpoints/crosses, and named SVA
assertions, yielding :class:`EvidenceCandidate` records (kind + fully-qualified
name) that the ingestion layer reconciles with the Evidence table.

The default implementation is a dependency-free regex scanner so it runs
anywhere. When ``pyslang`` is installed (the ``scan`` extra), a full-parser
backend can supersede it; the public API stays the same.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.models.enums import EvidenceKind

SV_SUFFIXES = (".sv", ".svh")

# class <name> extends <base> — a test if the base name ends in "test".
_CLASS_RE = re.compile(r"\bclass\s+(\w+)\s+extends\s+(\w+)", re.IGNORECASE)
_COVERGROUP_RE = re.compile(r"\bcovergroup\s+(\w+)(.*?)\bendgroup\b", re.IGNORECASE | re.DOTALL)
_COVERPOINT_RE = re.compile(r"\b(\w+)\s*:\s*coverpoint\b", re.IGNORECASE)
_CROSS_RE = re.compile(r"\b(\w+)\s*:\s*cross\b", re.IGNORECASE)
_ASSERT_RE = re.compile(r"\b(\w+)\s*:\s*assert\s+property\b", re.IGNORECASE)


@dataclass(frozen=True)
class EvidenceCandidate:
    kind: EvidenceKind
    fqn: str
    name: str
    meta: dict[str, Any] = field(default_factory=dict)


def _strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", " ", text)
    return text


def scan_text(text: str, *, source: str | None = None) -> list[EvidenceCandidate]:
    """Extract evidence candidates from one SystemVerilog source string."""
    code = _strip_comments(text)
    meta = {"source": source} if source else {}
    found: list[EvidenceCandidate] = []
    seen: set[tuple[EvidenceKind, str]] = set()

    def add(kind: EvidenceKind, fqn: str, name: str) -> None:
        key = (kind, fqn)
        if key not in seen:
            seen.add(key)
            found.append(EvidenceCandidate(kind=kind, fqn=fqn, name=name, meta=dict(meta)))

    for cls, base in _CLASS_RE.findall(code):
        if base.lower().endswith("test"):
            add(EvidenceKind.TEST, cls, cls)

    for cg_name, body in _COVERGROUP_RE.findall(code):
        for cp in _COVERPOINT_RE.findall(body):
            add(EvidenceKind.COVERPOINT, f"{cg_name}.{cp}", f"{cg_name}.{cp}")
        for cx in _CROSS_RE.findall(body):
            add(EvidenceKind.COVERPOINT, f"{cg_name}.{cx}", f"{cg_name}.{cx}")

    for label in _ASSERT_RE.findall(code):
        add(EvidenceKind.ASSERTION, label, label)

    return found


def scan_repo(root: str | Path) -> list[EvidenceCandidate]:
    """Recursively scan a repo path for SystemVerilog evidence."""
    root_path = Path(root)
    results: list[EvidenceCandidate] = []
    seen: set[tuple[EvidenceKind, str]] = set()
    for path in sorted(root_path.rglob("*")):
        if path.suffix.lower() not in SV_SUFFIXES or not path.is_file():
            continue
        rel = str(path.relative_to(root_path))
        for candidate in scan_text(path.read_text(encoding="utf-8", errors="ignore"), source=rel):
            key = (candidate.kind, candidate.fqn)
            if key not in seen:
                seen.add(key)
                results.append(candidate)
    return results
