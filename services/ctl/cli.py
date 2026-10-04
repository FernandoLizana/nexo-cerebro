"""Unified NEXO controller — foreground / background / config / params."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from services.runtime.config import (
    env_overrides,
    load_params_file,
    load_params_json,
    merge_params,
)
from services.runtime.process import spawn_background, status_background, stop_background

REPO_ROOT = Path(__file__).resolve().parents[2]

# Allowlisted module targets for background spawn (fail-closed).
SERVICE_SPECS: dict[str, dict] = {
    "dashboard": {
        "module": "services.dashboard.cli",
        "data_dir_key": "token_file_parent",
        "default_data": Path("data") / "nexo_dashboard",
        "long_running": True,
        "allow_params": frozenset({"host", "port", "token_file", "demo_nodes", "seed"}),
    },
    "node": {
        "module": "services.node.cli",
        "default_data": Path("data") / "nexo_node",
        "long_running": False,
        "allow_params": frozenset(
            {"data_dir", "name", "cpu_max", "ram_max_mb", "gpu", "job_id"}
        ),
    },
    "lab": {
        "module": "services.lab.cli",
        "default_data": Path("data") / "nexo_lab",
        "long_running": False,
        "allow_params": frozenset({"root", "seed", "lab_name", "devices"}),
    },
    "simulator": {
        "module": "services.simulator.cli",
        "default_data": Path("data") / "nexo_sim",
        "long_running": False,
        "allow_params": frozenset(
            {"nodes", "horizon", "seed", "beings_per_node", "memory_budget_bytes"}
        ),
    },
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexo-ctl",
        description=(
            "NEXO Collective Swarm controller — run tools in foreground or "
            "opt-in background, with --config / --params / env overrides."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run a Swarm service via console parameters")
    run.add_argument("service", choices=sorted(SERVICE_SPECS))
    run.add_argument(
        "service_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the service CLI (prefix with --)",
    )
    run.add_argument("--config", type=Path, default=None)
    run.add_argument("--params", default=None, help="Inline JSON object overrides")
    run.add_argument("--foreground", action="store_true", default=False)
    run.add_argument(
        "--background",
        "--detach",
        dest="background",
        action="store_true",
        default=False,
    )
    run.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Runtime record directory (default per service)",
    )

    st = sub.add_parser("status", help="Status of a background service")
    st.add_argument("service", choices=sorted(SERVICE_SPECS))
    st.add_argument("--data-dir", type=Path, default=None)

    stop = sub.add_parser("stop", help="Stop a background service (SIGTERM)")
    stop.add_argument("service", choices=sorted(SERVICE_SPECS))
    stop.add_argument("--data-dir", type=Path, default=None)

    lst = sub.add_parser("list", help="List controllable services and modes")
    lst.add_argument("--json", action="store_true")

    sub.add_parser("help-modes", help="Explain interaction modes")
    return parser


def _params_to_argv(service: str, params: dict) -> list[str]:
    """Translate merged params into CLI flags for known services."""
    argv: list[str] = []
    if service == "dashboard":
        if "host" in params:
            argv += ["--host", str(params["host"])]
        if "port" in params:
            argv += ["--port", str(params["port"])]
        if "token_file" in params:
            argv += ["--token-file", str(params["token_file"])]
        if "demo_nodes" in params:
            argv += ["--demo-nodes", str(params["demo_nodes"])]
        if "seed" in params:
            argv += ["--seed", str(params["seed"])]
        return argv
    if service == "node":
        # Default subcommand if caller did not pass one.
        return argv
    if service == "lab":
        return argv
    if service == "simulator":
        return argv
    return argv


def _forward_args(service_args: list[str]) -> list[str]:
    # argparse.REMAINDER keeps a leading "--" if the user typed it.
    args = list(service_args or [])
    if args and args[0] == "--":
        args = args[1:]
    return args


def _run_service(args: argparse.Namespace) -> int:
    spec = SERVICE_SPECS[args.service]
    file_params = load_params_file(args.config)
    inline = load_params_json(args.params)
    env = env_overrides("NEXO_")
    # Map common env aliases
    if "port" not in env and "NEXO_DASHBOARD_PORT" in __import__("os").environ:
        env["port"] = __import__("os").environ["NEXO_DASHBOARD_PORT"]
    params = merge_params(file_params, env, inline, allow=spec["allow_params"])

    data_dir = Path(args.data_dir) if args.data_dir else Path(spec["default_data"])
    if args.service == "dashboard" and "token_file" in params:
        data_dir = Path(params["token_file"]).parent

    forwarded = _forward_args(args.service_args)
    from_params = _params_to_argv(args.service, params)
    # For node/lab one-shots, ensure a subcommand exists when using only --params.
    if args.service == "node" and not forwarded:
        forwarded = ["status"]
        if params.get("name"):
            forwarded = ["start"]
    if args.service == "lab" and not forwarded:
        forwarded = ["rehearse"]
    if args.service == "simulator" and not forwarded:
        forwarded = ["run"]

    child_argv = [
        sys.executable,
        "-m",
        spec["module"],
        *from_params,
        *forwarded,
    ]
    # Force foreground in child when we detach via nexo-ctl.
    if args.background:
        if not spec["long_running"]:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": (
                            f"{args.service} is one-shot; use foreground. "
                            "Only long-running services may detach."
                        ),
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 2
        # Ensure child does not try to detach again.
        if "--background" not in child_argv and "--detach" not in child_argv:
            child_argv.append("--foreground")
        host = str(params.get("host") or "127.0.0.1")
        port = int(params["port"]) if "port" in params else 8765
        record = spawn_background(
            service=args.service,
            argv=child_argv,
            data_dir=data_dir,
            host=host,
            port=port,
            cwd=REPO_ROOT,
            extra={"params": params},
        )
        print(json.dumps({"ok": True, "mode": "background", "record": record.to_dict()}, indent=2))
        return 0

    # Foreground: import and run in-process for cleaner Windows experience.
    if args.service == "dashboard":
        from services.dashboard.cli import main as dash_main

        return int(dash_main(from_params + forwarded + (["--foreground"] if "--foreground" not in forwarded else [])))
    if args.service == "node":
        from services.node.cli import main as node_main

        return int(node_main(from_params + forwarded))
    if args.service == "lab":
        from services.lab.cli import main as lab_main

        return int(lab_main(from_params + forwarded))
    if args.service == "simulator":
        from services.simulator.cli import main as sim_main

        return int(sim_main(from_params + forwarded))
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        rows = [
            {
                "service": name,
                "long_running": spec["long_running"],
                "module": spec["module"],
                "modes": ["foreground", "console-args", "config", "params", "env"]
                + (["background"] if spec["long_running"] else []),
            }
            for name, spec in sorted(SERVICE_SPECS.items())
        ]
        if getattr(args, "json", False):
            print(json.dumps(rows, indent=2))
        else:
            for row in rows:
                modes = ", ".join(row["modes"])
                print(f"{row['service']:12}  {modes}")
        return 0

    if args.command == "help-modes":
        print(
            """
NEXO interaction modes
----------------------
1) Console parameters
   nexo-node start --name lab-a --cpu-max 40
   nexo-ctl run node -- start --name lab-a

2) Config file (YAML/JSON)
   nexo-ctl run dashboard --config configs/swarm/dashboard.local.yaml

3) Inline JSON params
   nexo-ctl run dashboard --params "{\\"port\\":8766,\\"seed\\":1}"

4) Environment overrides (prefix NEXO_)
   set NEXO_PORT=8766
   nexo-ctl run dashboard

5) Foreground (default for servers)
   nexo-dashboard --foreground
   nexo-ctl run dashboard --foreground

6) Background / detach (opt-in, long-running only)
   nexo-ctl run dashboard --background
   nexo-ctl status dashboard
   nexo-ctl stop dashboard

Security: dashboard binds loopback only; background never installs as a
Windows Service; silent packaging flags remain rejected.
""".strip()
        )
        return 0

    if args.command == "status":
        spec = SERVICE_SPECS[args.service]
        data_dir = Path(args.data_dir) if args.data_dir else Path(spec["default_data"])
        print(json.dumps(status_background(service=args.service, data_dir=data_dir), indent=2))
        return 0

    if args.command == "stop":
        spec = SERVICE_SPECS[args.service]
        data_dir = Path(args.data_dir) if args.data_dir else Path(spec["default_data"])
        print(json.dumps(stop_background(service=args.service, data_dir=data_dir), indent=2))
        return 0

    if args.command == "run":
        return _run_service(args)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
