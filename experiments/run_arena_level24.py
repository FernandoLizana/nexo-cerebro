"""
Runner Arena Level 2.4 — transfer + higiene + física.

Uso:
  python -m experiments.run_arena_level24 --seeds 2 --profile compact
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from experiments.arena.task_hygiene_unknown_bath import run_hygiene_unknown_bath_arm
from experiments.arena.task_physics_locomotion import run_physics_locomotion_smoke
from experiments.arena.task_transfer_fountain import run_transfer_fountain_arm
from experiments.gpu_env import enable_experiment_gpu, release_experiment_gpu
from experiments.process_guard import ensure_clean_pipeline, pipeline_root_pid


def run_all(seeds: int = 2, out_dir: Path | None = None) -> dict:
    out_dir = out_dir or Path("experiments/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    transfer_rows = []
    hygiene_rows = []
    for seed in range(seeds):
        for aff in (False, True):
            t = run_transfer_fountain_arm(seed, affordances=aff)
            transfer_rows.append(t)
            print(
                f"  transfer seed={seed} {t['condition']}: "
                f"exp2 ok={t['exposure2']['success']} ticks={t['exposure2']['ticks_to_drink']}"
            )
            h = run_hygiene_unknown_bath_arm(seed, affordances=aff)
            hygiene_rows.append(h)
            print(
                f"  hygiene seed={seed} {h['condition']}: "
                f"exp2 ok={h['exposure2']['success']} ticks={h['exposure2']['ticks_to_bathe']}"
            )
    phys = run_physics_locomotion_smoke(0)
    print(
        f"  physics: near={phys['drank_near']} far={phys['success_far']} "
        f"ticks={phys['ticks_far']} dist={phys['dist_final']}"
    )
    payload = {"transfer": transfer_rows, "hygiene": hygiene_rows, "physics": phys}
    (out_dir / "arena_level24.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Arena Level 2.4")
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
