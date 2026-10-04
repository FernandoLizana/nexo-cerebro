"""CLI for local in-process coordinator demos (no network server in S7)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from services.coordinator.auth import heartbeat_message, registration_message
from services.coordinator.service import Coordinator
from services.node.identity import load_or_create_identity


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nexo-coordinator",
        description="NEXO Coordinator S7 — in-process registry demo (no sockets).",
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data") / "nexo_node")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status-demo", help="Register local node, heartbeat, print status")
    args = parser.parse_args(argv)

    if args.command == "status-demo":
        coord = Coordinator()
        identity, private_key = load_or_create_identity(args.data_dir, node_name="demo-node")
        ch = coord.begin_registration(identity.node_id)
        sig = identity.sign(
            private_key,
            registration_message(identity.node_id, identity.node_name, ch["nonce"]),
        )
        coord.register_node(
            node_id=identity.node_id,
            node_name=identity.node_name,
            public_key_pem=identity.public_key_pem,
            software_version=identity.software_version,
            signature=sig,
        )
        ts = time.time()
        coord.heartbeat(
            node_id=identity.node_id,
            seq=1,
            ts=ts,
            signature=identity.sign(private_key, heartbeat_message(identity.node_id, 1, ts)),
            now=ts,
        )
        print(json.dumps(coord.status(), indent=2))
        return 0

    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
