"""Human-readable item IDs: ``{PREFIX}-{PROJECT}-{NNN}`` (e.g. REQ-PCIE-001).

Pure formatting + next-number logic. The database lookup for the current maximum
sequence lives in the repository layer; these helpers stay I/O-free.
"""

from __future__ import annotations

DEFAULT_WIDTH = 3


def next_sequence(current_max: int | None) -> int:
    """Return the next sequence number given the current maximum (or ``None``)."""
    return (current_max or 0) + 1


def format_human_id(prefix: str, project_key: str, seq: int, *, width: int = DEFAULT_WIDTH) -> str:
    """Compose a human ID, e.g. ``format_human_id("REQ", "pcie", 1) -> "REQ-PCIE-001"``."""
    if seq < 1:
        raise ValueError("sequence must be >= 1")
    return f"{prefix.upper()}-{project_key.upper()}-{seq:0{width}d}"
