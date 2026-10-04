"""H1.1 — corrida interactiva 24h con WorldDemoFacade + legacy_brain."""

from __future__ import annotations

import argparse
import json

from experiments.personal.h1_runner import export_payload, run_h1_interactive
from nexo.integrated_runtime import _repo_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="experiments.personal.run_h1_memory_interactive")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ticks", type=int, default=0, help="0 = 24h simuladas (288)")
    parser.add_argument("--ablation", default="integrated_full")
    args = parser.parse_args(argv)

    ticks = args.ticks or None
    payload = run_h1_interactive(seed=args.seed, ticks=ticks, ablation_id=args.ablation)
    out = _repo_root() / "results" / "personal" / "H1_memory" / f"h1_interactive_{args.ablation}_seed{args.seed}.json"
    summary = export_payload(payload, out)
    print(json.dumps({**summary, "encoding": payload["encoding"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
