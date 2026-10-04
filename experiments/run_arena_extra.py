"""
Arena Level 2.3 — hunger_unknown_bowl + dry_fountain.

Uso:
  python -m experiments.run_arena_extra --seeds 2 --profile compact
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from experiments.arena.task_dry_fountain import run_dry_fountain_failure
from experiments.arena.task_hunger_unknown_bowl import run_hunger_unknown_bowl_arm
from experiments.gpu_env import enable_experiment_gpu, release_experiment_gpu
from experiments.metrics import write_summary_csv
from experiments.process_guard import ensure_clean_pipeline, pipeline_root_pid


def run_all(seeds: int = 2, out_dir: Path | None = None) -> dict:
    out_dir = out_dir or Path("experiments/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    hunger_rows: list[dict] = []
    dry_rows: list[dict] = []
    for seed in range(seeds):
        for affordances in (False, True):
            row = run_hunger_unknown_bowl_arm(seed, affordances=affordances)
            hunger_rows.append(row)
            e2 = row["exposure2"]
            print(
                f"  Arena hunger seed={seed} {row['condition']}: "
                f"exp2_ticks={e2['ticks_to_eat']} ok={e2['success']} "
                f"hunger2={e2['hunger_delta']:+.2f}"
            )
        dry = run_dry_fountain_failure(seed)
        dry_rows.append(dry)
        print(
            f"  Arena dry seed={seed}: fails={dry['failure_count']} "
            f"gain={dry['mean_gain']:+.3f} thirst_d={dry['thirst_delta']:+.2f}"
        )

    flat_h = [
        {
            "seed": r["seed"],
            "condition": r["condition"],
            "exp2_ticks": r["exposure2"]["ticks_to_eat"],
            "exp2_success": r["exposure2"]["success"],
            "exp2_hunger_delta": r["exposure2"]["hunger_delta"],
            "records": r["affordance_records_final"],
        }
        for r in hunger_rows
    ]
    write_summary_csv(out_dir / "arena_hunger_unknown_bowl.csv", flat_h)
    (out_dir / "arena_extra.json").write_text(
        json.dumps({"hunger": hunger_rows, "dry": dry_rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"hunger": hunger_rows, "dry": dry_rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="Arena hunger + dry fountain")
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
