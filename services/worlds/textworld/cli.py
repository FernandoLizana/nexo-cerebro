"""CLI — run offline TextWorld experiments."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from services.being.store import BeingStore
from services.worlds.textworld.runner import run_textworld_experiment

DEFAULT_BEINGS = Path("data") / "nexo_node" / "beings"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nexo-textworld", description="Run TextWorld experiment (offline).")
    parser.add_argument("--beings-dir", type=Path, default=DEFAULT_BEINGS)
    parser.add_argument("--ids", nargs="+", required=True, help="Being ids to place")
    parser.add_argument("--ticks", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--experiment-id", default="textworld-local")
    args = parser.parse_args(argv)

    store = BeingStore(args.beings_dir)
    beings = [store.load(i) for i in args.ids]
    result = run_textworld_experiment(
        beings,
        seed=args.seed,
        ticks=args.ticks,
        experiment_id=args.experiment_id,
    )
    # Compact output for CLI
    out = {
        "ok": result["ok"],
        "experiment": result["experiment"],
        "snapshot": result["snapshot"],
        "event_count": result["event_count"],
        "interaction_count": result["interaction_count"],
        "trace_fingerprint": result["trace_fingerprint"],
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
