"""CLI to run the local read-only Swarm dashboard (S12)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from services.dashboard.app import create_app
from services.dashboard.auth import LocalDashboardAuth
from services.dashboard.telemetry import TelemetryHub
from services.runtime.args import add_background_arguments, add_params_arguments
from services.runtime.config import load_params_file, load_params_json, merge_params
from services.runtime.loopback import assert_loopback_host
from services.runtime.process import spawn_background, status_background, stop_background
from services.simulator.engine import DiscreteEventSimulator

DEFAULT_TOKEN = Path("data") / "nexo_dashboard" / "token.txt"
DEFAULT_DATA = Path("data") / "nexo_dashboard"
ALLOW_PARAMS = frozenset({"host", "port", "token_file", "demo_nodes", "seed"})


def _add_run_flags(parser: argparse.ArgumentParser) -> None:
    add_params_arguments(parser)
    add_background_arguments(parser)
    parser.add_argument("--host", default=None, help="Bind address (default loopback)")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--token-file", type=Path, default=None)
    parser.add_argument("--demo-nodes", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexo-dashboard",
        description="NEXO Dashboard S12 — local read-only telemetry (loopback).",
    )
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run", help="Start dashboard (also the default)")
    _add_run_flags(run)

    st = sub.add_parser("status", help="Background dashboard status")
    st.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)

    stop = sub.add_parser("stop", help="Stop background dashboard")
    stop.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)

    # Backward-compatible flat invocation: nexo-dashboard --port 8765
    _add_run_flags(parser)
    return parser


def _resolve_settings(args: argparse.Namespace) -> dict:
    file_params = load_params_file(getattr(args, "config", None))
    inline = load_params_json(getattr(args, "params", None))
    cli = {
        "host": getattr(args, "host", None),
        "port": getattr(args, "port", None),
        "token_file": str(args.token_file) if getattr(args, "token_file", None) else None,
        "demo_nodes": getattr(args, "demo_nodes", None),
        "seed": getattr(args, "seed", None),
    }
    merged = merge_params(file_params, inline, cli, allow=ALLOW_PARAMS)
    return {
        "host": str(merged.get("host") or "127.0.0.1"),
        "port": int(merged.get("port") or 8765),
        "token_file": Path(merged.get("token_file") or DEFAULT_TOKEN),
        "demo_nodes": int(merged.get("demo_nodes") or 12),
        "seed": int(merged.get("seed") or 42),
    }


def _serve(settings: dict) -> int:
    host = settings["host"]
    try:
        assert_loopback_host(host, context="dashboard bind")
    except ValueError as exc:
        print(str(exc))
        return 2

    auth = LocalDashboardAuth.load_or_create(settings["token_file"])
    sim = DiscreteEventSimulator(
        n_nodes=max(2, settings["demo_nodes"]),
        beings_per_node=2,
        seed=settings["seed"],
        memory_budget_bytes=8_000_000,
    )
    sim.seed_workload(horizon=40.0, interacts_per_node=2)
    sim.run_until(40.0)
    hub = TelemetryHub()
    hub.attach_simulator(sim)
    app = create_app(auth=auth, hub=hub)
    print(f"NEXO dashboard (read-only) on http://{host}:{settings['port']}/")
    print(f"Token file: {settings['token_file']}")
    print("Job injection: disabled")
    app.run(host=host, port=settings["port"], debug=False, use_reloader=False)
    return 0


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    # Flat mode: no subcommand -> treat as run
    if not raw or raw[0] not in {"run", "status", "stop", "-h", "--help"}:
        raw = ["run", *raw]

    parser = _build_parser()
    args = parser.parse_args(raw)
    command = args.command or "run"

    if command == "status":
        print(
            json.dumps(
                status_background(service="dashboard", data_dir=args.data_dir),
                indent=2,
            )
        )
        return 0
    if command == "stop":
        print(
            json.dumps(
                stop_background(service="dashboard", data_dir=args.data_dir),
                indent=2,
            )
        )
        return 0

    settings = _resolve_settings(args)
    data_dir = settings["token_file"].parent
    want_bg = bool(getattr(args, "background", False)) and os.environ.get(
        "NEXO_RUNTIME_FOREGROUND"
    ) != "1"

    if want_bg:
        child = [
            sys.executable,
            "-m",
            "services.dashboard.cli",
            "run",
            "--foreground",
            "--host",
            settings["host"],
            "--port",
            str(settings["port"]),
            "--token-file",
            str(settings["token_file"]),
            "--demo-nodes",
            str(settings["demo_nodes"]),
            "--seed",
            str(settings["seed"]),
        ]
        record = spawn_background(
            service="dashboard",
            argv=child,
            data_dir=data_dir,
            host=settings["host"],
            port=settings["port"],
            cwd=Path.cwd(),
        )
        print(
            json.dumps(
                {"ok": True, "mode": "background", "record": record.to_dict()},
                indent=2,
            )
        )
        return 0

    return _serve(settings)


if __name__ == "__main__":
    raise SystemExit(main())
