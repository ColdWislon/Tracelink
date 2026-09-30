"""Tests for the rtrack-push CLI scaffold (fake-data, dry-run)."""

from __future__ import annotations

import json

import pytest
from cli.rtrack_push.__main__ import main
from cli.rtrack_push.fake import fake_payload


def test_fake_payload_is_self_consistent() -> None:
    payload = fake_payload("pcie", external_id="#1842")
    assert payload["project_key"] == "pcie"
    assert payload["external_id"] == "#1842"
    kinds = {r["kind"] for r in payload["results"]}
    assert kinds == {"test", "coverpoint", "assertion"}


def test_dry_run_prints_payload(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["--project", "dma", "--fake", "--dry-run"])
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["project_key"] == "dma"


def test_without_fake_is_not_implemented() -> None:
    assert main(["--project", "pcie"]) == 2
