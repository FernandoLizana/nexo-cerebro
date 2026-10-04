"""CLI for federated learning research sandbox (S17)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from services.learning.federated.flags import FederatedResearchFlag
from services.learning.federated.service import FederatedResearchError, FederatedResearchService
from services.learning.federated.updates import ClientUpdate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nexo-fl",
        description="NEXO Federated Learning Research S17 — opt-in sandbox only.",
    )
    parser.add_argument("--root", type=Path, default=Path("data") / "nexo_fl")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--enable-research",
        action="store_true",
        help="Explicit opt-in (required). Default is off.",
    )
    parser.add_argument(
        "--acknowledge-risks",
        action="store_true",
        help="Acknowledge poisoning/privacy research risks.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Print FL research status")
    demo = sub.add_parser("demo-round", help="Run a tiny accepted/rejected demo round")
    demo.add_argument("--holdout-claim", default="berries grow near water")

    args = parser.parse_args(argv)
    flag = FederatedResearchFlag(
        enabled=bool(args.enable_research),
        acknowledge_risks=bool(args.acknowledge_risks),
    )
    try:
        svc = FederatedResearchService(args.root, research_flag=flag, seed=args.seed)
    except FederatedResearchError as exc:
        print(str(exc), file=sys.stderr)
        print("Pass --enable-research --acknowledge-risks", file=sys.stderr)
        return 2

    if args.command == "status":
        print(json.dumps(svc.status(), indent=2))
        return 0
    if args.command == "demo-round":
        svc.register_node("node-a")
        svc.register_node("node-b")
        rid = svc.begin_round()
        good = ClientUpdate(
            node_id="node-a",
            round_id=rid,
            weights={"berries": 0.4, "water": 0.3},
            lora_delta={"berries": 0.05},
            signature_hex="ab" * 32,
        )
        poison = ClientUpdate(
            node_id="node-b",
            round_id=rid,
            weights={"berries": float("nan")},
            signature_hex="cd" * 32,
        )
        print(json.dumps(svc.submit_update(good), indent=2))
        print(json.dumps(svc.submit_update(poison), indent=2))
        # Also reject null signature
        print(
            json.dumps(
                svc.submit_update(
                    ClientUpdate(
                        node_id="node-b",
                        round_id=rid,
                        weights={"water": 0.2},
                        signature_hex="00" * 32,
                    )
                ),
                indent=2,
            )
        )
        # Valid second update
        print(
            json.dumps(
                svc.submit_update(
                    ClientUpdate(
                        node_id="node-b",
                        round_id=rid,
                        weights={"water": 0.25, "meadow": 0.1},
                        signature_hex="ef" * 32,
                    )
                ),
                indent=2,
            )
        )
        result = svc.aggregate_round(holdout_claims=[{"claim": args.holdout_claim}])
        print(json.dumps(result, indent=2))
        return 0

    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
