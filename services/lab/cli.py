"""CLI for S15 multi-device lab rehearsals."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from services.lab.experiment_id import make_experiment_id
from services.lab.session import LabError, MultiDeviceLabSession
from services.lab.tls_policy import TlsLabPolicy, TlsPolicyError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nexo-lab",
        description="NEXO S15 multi-device lab — rehearsal, TLS policy, kill-switch checks.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    reh = sub.add_parser("rehearse", help="In-process ≥2-node lab rehearsal")
    reh.add_argument("--root", type=Path, default=Path("data") / "nexo_lab")
    reh.add_argument("--seed", type=int, default=15)
    reh.add_argument("--lab-name", default="s15-lab")

    eid = sub.add_parser("experiment-id", help="Print a reproducible experiment id")
    eid.add_argument("--lab-name", required=True)
    eid.add_argument("--seed", type=int, required=True)
    eid.add_argument("--devices", nargs="+", required=True)

    sub.add_parser("tls-policy", help="Print TLS lab policy JSON")

    args = parser.parse_args(argv)

    if args.command == "tls-policy":
        print(json.dumps(TlsLabPolicy().to_dict(), indent=2))
        return 0
    if args.command == "experiment-id":
        print(
            make_experiment_id(
                lab_name=args.lab_name,
                seed=args.seed,
                device_ids=list(args.devices),
            )
        )
        return 0
    if args.command == "rehearse":
        try:
            result = MultiDeviceLabSession(
                root=args.root,
                lab_name=args.lab_name,
                seed=args.seed,
            ).rehearse()
        except (LabError, TlsPolicyError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2))
        return 0

    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
