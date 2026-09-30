"""``rtrack-push`` — push regression/coverage results to Tracelink.

Scaffold with a ``--fake`` data mode. The real Cadence vManager session / IMC
coverage export is out of scope for this pass (Phase 3).
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

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
    parser.add_argument("--project", required=True, help="Target project key (e.g. pcie)")
    parser.add_argument("--url", default="http://localhost:8000", help="Tracelink base URL")
    parser.add_argument("--external-id", default="#1900", help="CI build / session id")
    parser.add_argument(
        "--fake", action="store_true", help="Generate fake data instead of exporting from Cadence"
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the payload without pushing")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.fake:
        print("Cadence vManager/IMC export is not implemented yet. Use --fake for now.")
        return 2

    payload = fake_payload(args.project, external_id=args.external_id)

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0

    endpoint = f"{args.url.rstrip('/')}/api/regression/runs"
    try:
        result = _post(endpoint, payload)
    except urllib.error.URLError as exc:
        print(f"Push failed: {exc}", file=sys.stderr)
        return 1
    print(f"Pushed {payload['project_key']} run: {json.dumps(result)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
