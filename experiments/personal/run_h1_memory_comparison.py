"""H1.2 — comparación integrated_full vs abl_no_memory (retención/promoción)."""

from __future__ import annotations

import argparse
import json

from experiments.personal.h1_runner import export_payload, run_h1_comparison
from nexo.integrated_runtime import _repo_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="experiments.personal.run_h1_memory_comparison")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ticks", type=int, default=288, help="Ticks por condición (default 288 = 24h)")
    args = parser.parse_args(argv)

    payload = run_h1_comparison(seed=args.seed, ticks=args.ticks)
    out = _repo_root() / "results" / "personal" / "H1_memory" / f"h1_comparison_seed{args.seed}.json"
    summary = export_payload(payload, out)
    print(json.dumps({**summary, "comparison": payload["comparison"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
