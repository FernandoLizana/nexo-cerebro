"""
E7 — Ablation multimodal: quitar visión degrada señal talámica y acercamiento.

Métricas:
  1) thalamic world/occipital gain (visión OFF → ↓)
  2) distancia a nevera con atención visual solo si visión ON

No fuerza choice_key.
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

TICKS = 20


def _fridge_dist(brain: InfantApeBrain) -> float:
    c = brain.world.furniture_center("fridge")
    if not c:
        return 999.0
    return float(np.hypot(brain.world.agent_x - c[0], brain.world.agent_y - c[1]))


def run_e7_arm(seed: int, *, ablate_vision: bool) -> dict:
    os.environ.setdefault("CEREBRO_OLLAMA", "0")
    enable_experiment_gpu()
    label = "no_vision" if ablate_vision else "full_sense"
    sd = Path(tempfile.mkdtemp(prefix=f"nexo_e7_{label}_{seed}_"))
    try:
        np.random.seed(seed)
        flags = replace(
            AblationFlags(),
            enable_multimodal_delays=True,
            enable_continuous_motor=True,
            enable_goal_stack=True,
            enable_td_reward=False,
            enable_grounding=False,
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
        fridge = brain.world.furniture_center("fridge")
        if fridge:
            # Misma habitación, ~120 px de la nevera
            brain.world.agent_x = float(fridge[0] - 110)
            brain.world.agent_y = float(fridge[1] + 20)
        else:
            brain.world.agent_x = 220.0
            brain.world.agent_y = 200.0
        brain.world.ensure_agent_free()
        brain.body.hunger = 0.92
        brain.body.thirst = 0.4

        if ablate_vision:
            brain.sensory_hub.set_ablation("vision")
            brain.world._attention_target = None  # noqa: SLF001
        else:
            brain.sensory_hub.clear_ablation()
            # Lock visual → meta de navegación (canal visión)
            if fridge:
                brain.world._attention_target = (float(fridge[0]), float(fridge[1]))  # noqa: SLF001

        # Un route para medir ganancias talámicas
        brain.sensory_hub.use_delays = True
        route = brain.sensory_hub.route(brain, brain._scan_vision())
        gain_world = float(brain.thalamus.gains.get("world", 1.0))
        gain_occ = float(brain.thalamus.gains.get("occipital", 1.0))

        d0 = _fridge_dist(brain)
        min_d = d0
        foodish = 0
        for _ in range(TICKS):
            # Reponer atención solo con visión (ablation la pierde)
            if not ablate_vision and fridge:
                brain.world._attention_target = (float(fridge[0]), float(fridge[1]))  # noqa: SLF001
            out = brain.world_tick(steps=1)
            min_d = min(min_d, _fridge_dist(brain))
            ck = str((out.get("deliberation") or {}).get("choice_key", ""))
            if ck in ("eat", "drink", "cook", "harvest"):
                foodish += 1

        d1 = _fridge_dist(brain)
        return {
            "seed": seed,
            "condition": label,
            "ablate_vision": ablate_vision,
            "dist_before": round(d0, 2),
            "dist_after": round(d1, 2),
            "dist_min": round(min_d, 2),
            "dist_delta": round(d0 - d1, 2),
            "thalamic_world_gain": round(gain_world, 4),
            "thalamic_occipital_gain": round(gain_occ, 4),
            "vision_gain_reported": route.get("vision_gain"),
            "foodish_choices": foodish,
            "ticks": TICKS,
            "choice_key_forced": False,
        }
    finally:
        release_experiment_gpu()
        shutil.rmtree(sd, ignore_errors=True)


def run_all_e7(seeds: int = 4, out_dir: Path | None = None) -> list[dict]:
    out_dir = out_dir or Path("experiments/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for seed in range(seeds):
        for ablate in (False, True):
            row = run_e7_arm(seed, ablate_vision=ablate)
            rows.append(row)
            print(
                f"  E7 seed={seed} {row['condition']}: "
                f"ddist={row['dist_delta']:+.1f} "
                f"world_g={row['thalamic_world_gain']:.2f}",
                flush=True,
            )
    write_summary_csv(out_dir / "e7_multimodal.csv", rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Nexo E7 multimodal ablation")
    parser.add_argument("--seeds", type=int, default=4)
    parser.add_argument("--out", default="experiments/results")
    parser.add_argument("--profile", default=None)
    args = parser.parse_args()
    if args.profile:
        os.environ["CEREBRO_EXPERIMENT_PROFILE"] = args.profile
    if not pipeline_root_pid():
        ensure_clean_pipeline()
    run_all_e7(seeds=args.seeds, out_dir=Path(args.out))


if __name__ == "__main__":
    main()
