"""
Runner Arena Level 2.5 — discriminación bueno/malo.

Uso:
  python -m experiments.run_arena_level25 --seeds 2 --profile compact
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from experiments.arena.task_discrimination import run_discrimination_good_vs_dry
from experiments.gpu_env import enable_experiment_gpu, release_experiment_gpu
from experiments.process_guard import ensure_clean_pipeline, pipeline_root_pid


def run_all(seeds: int = 2, out_dir: Path | None = None) -> list[dict]:
    out_dir = out_dir or Path("experiments/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for seed in range(seeds):
        for aff in (False, True):
            row = run_discrimination_good_vs_dry(seed, affordances=aff)
            rows.append(row)
            print(
                f"  discrim seed={seed} {row['condition']}: "
                f"drank={row['drank_success']} ticks={row['ticks']} "
                f"goal_good={row['goal_is_good']} pref_good={row['preferred_good']} "
                f"dG={row['dist_good']} dD={row['dist_dry']}"
            )
    (out_dir / "arena_discrimination.json").write_text(
        json.dumps({"rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Arena Level 2.5 discrimination")
    parser.add_argument("--seeds", type=int, default=2)
    parser.add_argument("--profile", default="compact")
    parser.add_argument("--out", default="experiments/results")
    args = parser.parse_args()
    os.environ.setdefault("CEREBRO_OLLAMA", "0")
    os.environ["CEREBRO_EXPERIMENT_PROFILE"] = args.profile
    os.environ.setdefault("CEREBRO_SKIP_PROCESS_GUARD", "1")
    if not pipeline_root_pid():
        ensure_clean_pipeline()
    enable_experiment_gpu()
    try:
        run_all(seeds=args.seeds, out_dir=Path(args.out))
    finally:
        release_experiment_gpu()


if __name__ == "__main__":
    main()
