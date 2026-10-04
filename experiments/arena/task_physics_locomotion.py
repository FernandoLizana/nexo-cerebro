"""
Arena Level 2.4 — física sin arena_fast_locomotion (smoke).

Comprueba que walk_goal + gain biomecánico permite alcanzar la fuente
en presupuesto amplio. No escribe choice_key.
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

FOUNTAIN_XY = (265.0, 250.0)
NEAR_XY = (275.0, 255.0)
FAR_XY = (360.0, 200.0)  # más cerca que thirst clássico: física es más lenta
MAX_TICKS = 160


def run_physics_locomotion_smoke(seed: int = 0) -> dict[str, Any]:
    sd = Path(tempfile.mkdtemp(prefix=f"nexo_physics_{seed}_"))
    flags = replace(
        AblationFlags(),
        enable_affordance_learning=True,
        disable_hippocampus=True,
        enable_td_reward=False,
        enable_continuous_motor=False,
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
    fu = brain.world.ensure_novel_fountain(
        x=FOUNTAIN_XY[0], y=FOUNTAIN_XY[1], object_id="phys-fountain"
    )
    brain.world.water_only_novel = True
    brain.world.arena_fast_locomotion = False  # física real
    brain.world.agent_x = float(NEAR_XY[0])
    brain.world.agent_y = float(NEAR_XY[1])
    brain.world.ensure_agent_free()
    brain.body.thirst = 0.9
    brain.body.hunger = 0.1
    thirst0 = float(brain.body.thirst)

    # Exp1: aprender cerca.
    drank_near = False
    for _ in range(40):
        brain.world_tick(steps=1)
        if float(brain.body.thirst) < thirst0 - 0.08:
            drank_near = True
            break

    brain.world.agent_x = float(FAR_XY[0])
    brain.world.agent_y = float(FAR_XY[1])
    brain.world.ensure_agent_free()
    brain.world.clear_walk_goal()
    brain.body.thirst = 0.9
    thirst1 = float(brain.body.thirst)
    ticks = None
    for t in range(1, MAX_TICKS + 1):
        brain.world_tick(steps=1)
        if float(brain.body.thirst) < thirst1 - 0.08:
            ticks = t
            break

    dist = float(
        np.hypot(
            brain.world.agent_x - (fu.x + fu.w / 2),
            brain.world.agent_y - (fu.y + fu.h / 2),
        )
    )
    return {
        "seed": seed,
        "drank_near": drank_near,
        "success_far": ticks is not None,
        "ticks_far": ticks if ticks is not None else MAX_TICKS,
        "dist_final": round(dist, 2),
        "arena_fast_locomotion": False,
        "agency_note": "Physics path; PFC alone writes choice_key",
    }
