"""
Runner Arena Level 2.2 — thirst_unknown_water.

Uso:
  python -m experiments.run_arena_thirst --seeds 3 --profile compact
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from experiments.arena import run_thirst_unknown_water_arm, summarize_thirst_rows
from experiments.gpu_env import enable_experiment_gpu, release_experiment_gpu
from experiments.metrics import write_summary_csv
from experiments.process_guard import ensure_clean_pipeline, pipeline_root_pid


def run_all(seeds: int = 3, out_dir: Path | None = None) -> list[dict]:
    out_dir = out_dir or Path("experiments/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for seed in range(seeds):
        for affordances in (False, True):
            row = run_thirst_unknown_water_arm(seed, affordances=affordances)
            rows.append(row)
            e1 = row["exposure1"]
            e2 = row["exposure2"]
            print(
                f"  Arena thirst seed={seed} {row['condition']}: "
                f"exp1_ticks={e1['ticks_to_drink']} ok={e1['success']} "
                f"exp2_ticks={e2['ticks_to_drink']} ok={e2['success']} "
                f"records={row['affordance_records_final']} "
                f"thirst2={e2['thirst_delta']:+.2f}"
            )
    summary = summarize_thirst_rows(rows)
    flat = []
    for row in rows:
        flat.append(
            {
                "seed": row["seed"],
                "condition": row["condition"],
                "affordances": row["affordances"],
                "exp1_ticks": row["exposure1"]["ticks_to_drink"],
                "exp1_success": row["exposure1"]["success"],
                "exp2_ticks": row["exposure2"]["ticks_to_drink"],
                "exp2_success": row["exposure2"]["success"],
                "exp2_thirst_delta": row["exposure2"]["thirst_delta"],
                "affordance_records": row["affordance_records_final"],
                "agency_violations": row["exposure2"]["agency_violations"],
            }
        )
    write_summary_csv(out_dir / "arena_thirst_unknown_water.csv", flat)
    (out_dir / "arena_thirst_unknown_water.json").write_text(
        json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("  summary:", summary)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Arena thirst_unknown_water")
    parser.add_argument("--seeds", type=int, default=3)
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
