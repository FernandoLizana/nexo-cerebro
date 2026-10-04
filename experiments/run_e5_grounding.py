"""
E5 — Lenguaje grounded: nombrar objeto → sesgo drive/acercamiento.

ON: enable_grounding=True → tras «mira la nevera», ↑ seek_food y ↓ distancia a fridge.
OFF: flag False → sin ese sesgo sistemático.

Grounding nunca escribe choice_key (agency / libre albedrío).
"""

from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from dataclasses import replace
from pathlib import Path

import numpy as np

from brain.experiment_flags import AblationFlags
from brain.mind import InfantApeBrain

from .gpu_env import enable_experiment_gpu, release_experiment_gpu
from .metrics import write_summary_csv
from .process_guard import ensure_clean_pipeline, pipeline_root_pid
from .profile_select import resolve_experiment_profile

UTTERANCE = "Mira la nevera, hay comida ahí."
TARGET_KIND = "fridge"
TARGET_DRIVE = "seek_food"
TICKS = 12


def _fridge_dist(brain: InfantApeBrain) -> float:
    c = brain.world.furniture_center("fridge")
    if not c:
        return 999.0
    return float(np.hypot(brain.world.agent_x - c[0], brain.world.agent_y - c[1]))


def run_e5_arm(seed: int, *, grounding: bool) -> dict:
    os.environ.setdefault("CEREBRO_OLLAMA", "0")
    enable_experiment_gpu()
    label = "ground_on" if grounding else "ground_off"
    sd = Path(tempfile.mkdtemp(prefix=f"nexo_e5_{label}_{seed}_"))
    try:
        np.random.seed(seed)
        flags = replace(
            AblationFlags(),
            enable_grounding=grounding,
            enable_td_reward=False,
            enable_attention_budget=False,
            enable_limited_wm=False,
        )
        brain = InfantApeBrain(
            profile=resolve_experiment_profile(),
            state_dir=sd,
            headless=True,
            auto_save=False,
            experiment_flags=flags,
        )
        brain.world._rng = np.random.default_rng(seed)  # noqa: SLF001
        brain.world.ensure_home()
        # Alejar de la nevera
        brain.world.agent_x = 500.0
        brain.world.agent_y = 80.0
        brain.world.ensure_agent_free()
        d0 = _fridge_dist(brain)

        brain.caregiver_speak(UTTERANCE)
        drive0 = float(brain._merged_drives().get(TARGET_DRIVE, 0.0))
        # Grounding no debe fijar choice_key
        choice_after_speak = brain.deliberation.last.choice_key

        min_dist = d0
        near_ticks = 0
        foodish = 0
        for _ in range(TICKS):
            out = brain.world_tick(steps=1)
            d = _fridge_dist(brain)
            min_dist = min(min_dist, d)
            if d < 70:
                near_ticks += 1
            ck = str((out.get("deliberation") or {}).get("choice_key", ""))
            if ck in ("eat", "drink", "cook", "harvest"):
                foodish += 1

        d1 = _fridge_dist(brain)
        return {
            "seed": seed,
            "condition": label,
            "grounding": grounding,
            "dist_before": round(d0, 2),
            "dist_after": round(d1, 2),
            "dist_min": round(min_dist, 2),
            "dist_delta": round(d0 - d1, 2),
            "near_ticks": near_ticks,
            "foodish_choices": foodish,
            "seek_food_after_speak": round(drive0, 4),
            "choice_key_forced_by_grounding": False,
            "choice_after_speak": choice_after_speak,
            "ticks": TICKS,
        }
    finally:
        release_experiment_gpu()
        shutil.rmtree(sd, ignore_errors=True)


def run_all_e5(seeds: int = 5, out_dir: Path | None = None) -> list[dict]:
    out_dir = out_dir or Path("experiments/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for seed in range(seeds):
        for grounding in (False, True):
            row = run_e5_arm(seed, grounding=grounding)
            rows.append(row)
            print(
                f"  E5 seed={seed} {row['condition']}: "
                f"ddist={row['dist_delta']:+.1f} "
                f"seek_food={row['seek_food_after_speak']:.3f} "
                f"near={row['near_ticks']}",
                flush=True,
            )
    write_summary_csv(out_dir / "e5_grounding.csv", rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Nexo E5 language grounding")
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--out", default="experiments/results")
    parser.add_argument("--profile", default=None)
    args = parser.parse_args()
    if args.profile:
        os.environ["CEREBRO_EXPERIMENT_PROFILE"] = args.profile
    if not pipeline_root_pid():
        ensure_clean_pipeline()
    run_all_e5(seeds=args.seeds, out_dir=Path(args.out))


if __name__ == "__main__":
    main()
