"""CLI for the opt-in mobile lab gateway."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from services.lab_gateway.server import approve_node, enqueue_job, start_gateway, stop_gateway
from services.lab_gateway.store import GatewayStore

DEFAULT_ROOT = Path("data") / "nexo_lab_gateway"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nexo-lab-gateway")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start")
    start.add_argument("--enable-mobile-lab", action="store_true")
    start.add_argument("--acknowledge-risks", action="store_true")
    start.add_argument("--host", required=True)
    start.add_argument("--port", type=int, default=8767)
    start.add_argument("--lab-id", default="local-lab")
    start.add_argument("--allow-loopback", action="store_true")
    start.add_argument("--foreground", action="store_true")

    sub.add_parser("pairing-code")
    sub.add_parser("nodes")
    approve = sub.add_parser("approve")
    approve.add_argument("node_id")
    revoke = sub.add_parser("revoke")
    revoke.add_argument("node_id")
    job = sub.add_parser("enqueue")
    job.add_argument("node_id")
    job.add_argument("job_type")
    sub.add_parser("stop")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.root
    if args.command == "start":
        from services.lab_gateway.certs import load_or_create_lab_cert
        from services.lab_gateway.policy import assert_explicit_private_host, flags_required

        refused = flags_required(args.enable_mobile_lab, args.acknowledge_risks)
        if refused:
            print(json.dumps({"ok": False, "error": refused}))
            return 2
        host = assert_explicit_private_host(args.host, allow_loopback=args.allow_loopback)
        start_gateway(
            host=host,
            port=args.port,
            root=root,
            enable_mobile_lab=True,
            acknowledge_risks=True,
            allow_loopback=args.allow_loopback,
            lab_id=args.lab_id,
        )
        _cert, _key, fingerprint = load_or_create_lab_cert(root, host=host)
        store = GatewayStore(root)
        pairing = store.issue_pairing(host=host, port=args.port, fingerprint=fingerprint, lab_id=args.lab_id)
        print(json.dumps({"ok": True, "pairing": pairing, "note": "paste this JSON into the phone; no camera permission"}, indent=2))
        if args.foreground:
            try:
                while not GatewayStore(root).state.get("stopped"):
                    time.sleep(0.5)
            except KeyboardInterrupt:
                stop_gateway(root)
        return 0
    if args.command == "pairing-code":
        path = root / "pairing.json"
        print(path.read_text(encoding="utf-8") if path.is_file() else json.dumps({"ok": False, "error": "no active code"}))
        return 0
    if args.command == "nodes":
        store = GatewayStore(root)
        print(json.dumps({"pending": store.state.get("pending"), "nodes": store.state.get("nodes"), "experiences": store.state.get("experiences")}, indent=2))
        return 0
    if args.command == "approve":
        print(json.dumps({"ok": True, "node": approve_node(root, args.node_id)}, indent=2))
        return 0
    if args.command == "revoke":
        store = GatewayStore(root)
        node = store.state["nodes"].get(args.node_id)
        if node:
            node["status"] = "revoked"
        store.save()
        print(json.dumps({"ok": True, "revoked": args.node_id}))
        return 0
    if args.command == "enqueue":
        print(json.dumps(enqueue_job(root, args.node_id, args.job_type, {"engine": "creature-mobile-tier0-v1"}), indent=2))
        return 0
    if args.command == "stop":
        stop_gateway(root)
        print(json.dumps({"ok": True, "stopped": True}))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
