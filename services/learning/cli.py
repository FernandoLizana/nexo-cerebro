"""CLI for collective learning sandboxes (S16)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from services.learning.service import CollectiveLearningError, CollectiveLearningService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nexo-learn",
        description="NEXO Collective Learning S16 — sandbox A/B, manual promote, rollback.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("data") / "nexo_learning",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ab = sub.add_parser("run-ab", help="Distill Phase A and B from claims JSONL/list")
    ab.add_argument("--claims-json", type=Path, required=True, help="JSON list of {claim, confidence}")

    ev = sub.add_parser("evaluate", help="Run eval gates on an artifact")
    ev.add_argument("--id", required=True)

    promo = sub.add_parser("promote", help="Manually promote an EVAL_PASSED artifact")
    promo.add_argument("--id", required=True)

    sub.add_parser("rollback", help="Restore previous promoted artifact")
    sub.add_parser("status", help="Print active artifact / policy")

    args = parser.parse_args(argv)
    svc = CollectiveLearningService(args.root)

    try:
        if args.command == "run-ab":
            claims = json.loads(args.claims_json.read_text(encoding="utf-8"))
            print(json.dumps(svc.run_ab(claims=claims), indent=2))
            return 0
        if args.command == "evaluate":
            print(json.dumps(svc.evaluate(args.id), indent=2))
            return 0
        if args.command == "promote":
            art = svc.promote(args.id)
            print(json.dumps(art.to_dict(), indent=2))
            return 0
        if args.command == "rollback":
            art = svc.rollback()
            print(json.dumps(art.to_dict(), indent=2))
            return 0
        if args.command == "status":
            print(json.dumps(svc.status(), indent=2))
            return 0
    except CollectiveLearningError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
