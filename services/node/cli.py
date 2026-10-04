"""CLI for voluntary NEXO Node (S2) — local only, no coordinator connection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from services.node.governor import ResourceLimits
from services.node.jobs import JobRequest
from services.node.runtime import NodeRuntime
from services.runtime.args import add_params_arguments
from services.runtime.config import load_params_file, load_params_json, merge_params

DEFAULT_DATA = Path("data") / "nexo_node"
ALLOW_PARAMS = frozenset({"data_dir", "name", "cpu_max", "ram_max_mb", "gpu", "job_id"})


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexo-node",
        description="NEXO Node — voluntary local cognitive-agent laboratory runtime (no network in S2).",
    )
    add_params_arguments(parser)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Directory for identity keys and node state (default: data/nexo_node)",
    )
    common.add_argument("--name", default=None, help="Human-readable node name")
    common.add_argument("--cpu-max", type=float, default=None, help="Max CPU percent budget")
    common.add_argument("--ram-max-mb", type=int, default=None, help="Max RAM MB budget")
    common.add_argument("--gpu", action="store_true", default=None, help="Allow GPU jobs (owner opt-in)")

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("start", parents=[common], help="Create/load identity and mark node RUNNING")
    sub.add_parser("status", parents=[common], help="Print public node status (never prints private key)")
    sub.add_parser("stop", parents=[common], help="STOP NEXO NODE kill switch")
    sub.add_parser("pause", parents=[common], help="Pause accepting jobs")
    sub.add_parser("resume", parents=[common], help="Resume after pause")
    check = sub.add_parser(
        "self-check", parents=[common], help="Run allowlisted RUN_NODE_SELF_CHECK job"
    )
    check.add_argument("--job-id", default=None)
    return parser


def _resolve(args: argparse.Namespace) -> dict:
    file_params = load_params_file(args.config)
    inline = load_params_json(args.params)
    cli = {
        "data_dir": str(args.data_dir) if args.data_dir else None,
        "name": args.name,
        "cpu_max": args.cpu_max,
        "ram_max_mb": args.ram_max_mb,
        "gpu": True if args.gpu else None,
        "job_id": getattr(args, "job_id", None),
    }
    merged = merge_params(file_params, inline, cli, allow=ALLOW_PARAMS)
    return {
        "data_dir": Path(merged.get("data_dir") or DEFAULT_DATA),
        "name": str(merged.get("name") or "local-node"),
        "cpu_max": float(merged.get("cpu_max") or 50.0),
        "ram_max_mb": int(merged.get("ram_max_mb") or 2048),
        "gpu": bool(merged.get("gpu") or False),
        "job_id": str(merged.get("job_id") or "self-check-1"),
    }


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    cfg = _resolve(args)
    limits = ResourceLimits(
        cpu_max_percent=cfg["cpu_max"],
        ram_max_mb=cfg["ram_max_mb"],
        gpu_enabled=bool(cfg["gpu"]),
    )
    runtime = NodeRuntime(data_dir=cfg["data_dir"], node_name=cfg["name"], limits=limits)

    if args.command == "start":
        identity = runtime.start()
        print(json.dumps({"ok": True, "identity": identity.public_dict()}, indent=2))
        return 0

    if args.command == "status":
        if runtime.state_path.is_file():
            print(runtime.state_path.read_text(encoding="utf-8"))
        else:
            print(json.dumps({"ok": False, "error": "node not started yet"}, indent=2))
        return 0

    if args.command == "stop":
        runtime.start()
        snapshot = runtime.kill_switch()
        print(json.dumps({"ok": True, "stopped": snapshot}, indent=2))
        return 0

    if args.command == "pause":
        runtime.start()
        runtime.pause()
        print(json.dumps({"ok": True, "state": runtime.state.value}, indent=2))
        return 0

    if args.command == "resume":
        runtime.start()
        runtime.resume()
        print(json.dumps({"ok": True, "state": runtime.state.value}, indent=2))
        return 0

    if args.command == "self-check":
        runtime.start()
        result = runtime.submit_job(
            JobRequest(job_type="RUN_NODE_SELF_CHECK", job_id=cfg["job_id"], payload={})
        )
        print(json.dumps(result, indent=2))
        return 0

    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
