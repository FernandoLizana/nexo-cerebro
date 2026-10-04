"""
Arena: hambre + cuenco desconocido (1ª vs 2ª exposición).

Misma lógica que thirst: sin affordances no hay GPS al cuenco.
"""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from brain.experiment_flags import AblationFlags
from brain.mind import InfantApeBrain
from experiments.profile_select import resolve_experiment_profile

BOWL_XY = (310.0, 240.0)
NEAR_XY = (320.0, 245.0)
FAR_XY = (420.0, 160.0)
EXPOSURE1_TICKS = 36
EXPOSURE2_TICKS = 90


def _dist_to_bowl(brain: InfantApeBrain) -> float:
    c = brain.world.furniture_center("food_bowl")
    if not c:
        return 999.0
    return float(np.hypot(brain.world.agent_x - c[0], brain.world.agent_y - c[1]))


def _bowl_obs(brain: InfantApeBrain) -> int:
    return int(
        sum(
            r.observation_count
            for r in brain.affordance_map.records.values()
            if r.object_type == "food_bowl" and r.candidate_key == "eat"
        )
    )


def _setup(seed: int, *, affordances: bool, state_dir: Path) -> InfantApeBrain:
    flags = replace(
        AblationFlags(),
        enable_affordance_learning=affordances,
        enable_neural_telemetry=True,
        enable_counterfactual=affordances,
        enable_td_reward=False,
        enable_grounding=False,
        enable_continuous_motor=False,
        disable_hippocampus=True,
    )
    brain = InfantApeBrain(
        profile=resolve_experiment_profile(),
        state_dir=state_dir,
        headless=True,
        auto_save=False,
        experiment_flags=flags,
    )
    brain.world._rng = np.random.default_rng(seed)  # noqa: SLF001
    brain.world.ensure_home()
    brain.world.ensure_novel_food_bowl(
        x=BOWL_XY[0], y=BOWL_XY[1], object_id="novel-bowl", label="cuenco desconocido"
    )
    brain.world.food_only_novel = True
    brain.world.arena_fast_locomotion = True
    brain.body.thirst = 0.12
    brain.body.fatigue = 0.15
    brain.body.comfort = 0.45
    return brain


def _prime(brain: InfantApeBrain, *, x: float, y: float) -> None:
    brain.world.agent_x = float(x)
    brain.world.agent_y = float(y)
    brain.world.ensure_agent_free()
    brain.world.clear_walk_goal()
    brain.body.hunger = 0.88
    brain.body.thirst = 0.12


def _run_until_eat(brain: InfantApeBrain, *, max_ticks: int) -> dict[str, Any]:
    hunger0 = float(brain.body.hunger)
    obs0 = _bowl_obs(brain)
    min_dist = _dist_to_bowl(brain)
    ticks: int | None = None
    for t in range(1, max_ticks + 1):
        brain.world_tick(steps=1)
        min_dist = min(min_dist, _dist_to_bowl(brain))
        if float(brain.body.hunger) <= hunger0 - 0.08 or _bowl_obs(brain) > obs0:
            ticks = t
            break
    success = ticks is not None and float(brain.body.hunger) < hunger0 - 0.05
    return {
        "success": bool(success),
        "ticks_to_eat": ticks if ticks is not None else max_ticks,
        "hunger_delta": round(hunger0 - float(brain.body.hunger), 4),
        "dist_min": round(float(min_dist), 2),
        "affordance_observations": _bowl_obs(brain),
        "agency_violations": 0,
        "max_ticks": max_ticks,
    }


def run_hunger_unknown_bowl_arm(seed: int, *, affordances: bool) -> dict[str, Any]:
    label = "aff_on" if affordances else "aff_off"
    sd = Path(tempfile.mkdtemp(prefix=f"nexo_arena_hunger_{label}_{seed}_"))
    brain = _setup(seed, affordances=affordances, state_dir=sd)
    _prime(brain, x=NEAR_XY[0], y=NEAR_XY[1])
    exp1 = _run_until_eat(brain, max_ticks=EXPOSURE1_TICKS)
    records_after_1 = len(brain.affordance_map.records)
    _prime(brain, x=FAR_XY[0], y=FAR_XY[1])
    exp2 = _run_until_eat(brain, max_ticks=EXPOSURE2_TICKS)
    return {
        "seed": seed,
        "condition": label,
        "affordances": affordances,
        "exposure1": exp1,
        "exposure2": exp2,
        "affordance_records_after_exp1": records_after_1,
        "affordance_records_final": len(brain.affordance_map.records),
        "agency_note": "Hunger arena; PFC alone writes choice_key",
    }
