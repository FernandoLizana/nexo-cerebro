"""CLI for Creature Engine simulations (local, no LLM, no network)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from services.being.store import BeingStore
from services.creature.engine import run_creature_ticks

DEFAULT_BEINGS = Path("data") / "nexo_node" / "beings"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nexo-creature", description="Run Creature Engine ticks (no LLM).")
    parser.add_argument("--beings-dir", type=Path, default=DEFAULT_BEINGS)
    parser.add_argument("--id", required=True, dest="being_id")
    parser.add_argument("--ticks", type=int, default=30)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    store = BeingStore(args.beings_dir)
    being = store.load(args.being_id)
    result = run_creature_ticks(being, ticks=args.ticks, seed=args.seed)
    store.save(being)
    # Compact stdout
    out = {
        "ok": result["ok"],
        "being_id": result["being_id"],
        "ticks": result["ticks"],
        "seed": result["seed"],
        "final_state": result["final_state"],
        "final_drives": result["final_drives"],
        "llm_used": False,
        "actions": [t["action"] for t in result["trajectory"]],
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
