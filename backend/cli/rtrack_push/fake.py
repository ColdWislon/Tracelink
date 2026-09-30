"""Generate a plausible fake regression payload (stand-in for Cadence export)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def fake_payload(project_key: str, *, external_id: str = "#1900") -> dict[str, Any]:
    """A small, self-consistent regression payload for ``project_key``."""
    now = datetime.now(UTC).isoformat()
    results: list[dict[str, Any]] = [
        {
            "kind": "test",
            "fqn": f"{project_key}_smoke_test",
            "passed": 20,
            "failed": 0,
            "total": 20,
        },
        {
            "kind": "test",
            "fqn": f"{project_key}_stress_test",
            "passed": 14,
            "failed": 2,
            "total": 20,
        },
        {"kind": "coverpoint", "fqn": f"cg_{project_key}.cp_mode", "hits": 100, "goal": 100},
        {"kind": "coverpoint", "fqn": f"cg_{project_key}.cp_edge", "hits": 62, "goal": 100},
        {"kind": "assertion", "fqn": f"a_{project_key}_no_overflow", "fired": 4210, "failed": 0},
    ]
    return {
        "project_key": project_key,
        "source": "jenkins",
        "external_id": external_id,
        "started_at": now,
        "finished_at": now,
        "results": results,
    }
