"""Tests for the rtrack-push CLI (fake-data + file modes, dry-run)."""

from __future__ import annotations

import json
from pathlib import Path

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


def test_requires_a_source_mode() -> None:
    # Neither --fake nor --file -> argparse errors out.
    with pytest.raises(SystemExit):
        main(["--project", "pcie"])


def test_file_mode_dry_run(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"project_key": "irq", "results": []}
    path = tmp_path / "run.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    code = main(["--file", str(path), "--dry-run"])
    assert code == 0
    assert json.loads(capsys.readouterr().out)["project_key"] == "irq"


def test_fake_requires_project() -> None:
    assert main(["--fake"]) == 2
