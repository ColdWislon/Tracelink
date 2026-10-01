"""``rtrack-push`` — push regression/coverage results to Tracelink.

Two input modes:
  --fake              generate a small self-consistent payload (demo / smoke test)
  --file PATH         push a prepared JSON payload (the export a CI job produces)

The real Cadence vManager session / IMC coverage *export* that would produce that
JSON is out of scope for this pass; the payload schema is documented at
``GET /api/regression/schema``.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from cli.rtrack_push.fake import fake_payload


def _post(url: str, payload: dict[str, object]) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(request) as response:  # noqa: S310 (local dev tool)
        result: dict[str, object] = json.loads(response.read().decode("utf-8"))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rtrack-push", description=__doc__)
    parser.add_argument("--url", default="http://localhost:8000", help="Tracelink base URL")
    parser.add_argument("--project", help="Target project key (required with --fake)")
    parser.add_argument("--external-id", default="#1900", help="CI build / session id (fake mode)")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fake", action="store_true", help="Generate a fake payload")
    source.add_argument("--file", type=Path, help="Push a prepared JSON payload file")
    parser.add_argument("--dry-run", action="store_true", help="Print the payload without pushing")
    return parser


def _load_payload(args: argparse.Namespace) -> dict[str, Any] | None:
    if args.fake:
        if not args.project:
            print("--project is required with --fake", file=sys.stderr)
            return None
        return fake_payload(args.project, external_id=args.external_id)
    try:
        data: dict[str, Any] = json.loads(Path(args.file).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Could not read payload: {exc}", file=sys.stderr)
        return None
    return data


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    payload = _load_payload(args)
    if payload is None:
        return 2

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0

    endpoint = f"{args.url.rstrip('/')}/api/regression/runs"
    try:
        result = _post(endpoint, payload)
    except urllib.error.URLError as exc:
        print(f"Push failed: {exc}", file=sys.stderr)
        return 1
    print(f"Pushed run: {json.dumps(result)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
