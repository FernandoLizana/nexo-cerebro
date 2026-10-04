"""CLI for Swarm Simulator load rehearsals (S11)."""

from __future__ import annotations

import argparse
import json
import sys

from services.simulator.engine import DiscreteEventSimulator
from services.simulator.metrics import load_curve_table


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nexo-simulator",
        description=(
            "NEXO Swarm Simulator S11 — discrete-event logical nodes "
            "(no sockets; not real multi-device proof)."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Seed workload and run until horizon")
    run.add_argument("--nodes", type=int, default=10)
    run.add_argument("--beings-per-node", type=int, default=2)
    run.add_argument("--horizon", type=float, default=50.0)
    run.add_argument("--interacts-per-node", type=int, default=2)
    run.add_argument("--seed", type=int, default=42)
    run.add_argument("--memory-budget", type=int, default=8_000_000)

    sub.add_parser("load-curves", help="Print documented load curve envelopes")

    args = parser.parse_args(argv)

    if args.command == "load-curves":
        print(json.dumps(load_curve_table(), indent=2))
        return 0
    if args.command == "run":
        sim = DiscreteEventSimulator(
            n_nodes=args.nodes,
            beings_per_node=args.beings_per_node,
            seed=args.seed,
            memory_budget_bytes=args.memory_budget,
        )
        sim.seed_workload(horizon=args.horizon, interacts_per_node=args.interacts_per_node)
        metrics = sim.run_until(args.horizon)
        print(json.dumps({"status": sim.status(), "metrics": metrics.to_dict()}, indent=2))
        return 0 if metrics.within_memory_budget else 1

    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
