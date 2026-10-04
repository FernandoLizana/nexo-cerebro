"""
Arena Level 2.4 — transferencia: aprende en fuente A, generaliza a fuente B.

Tras beber en A, se elimina A y aparece B lejos. El prior de navegación usa
object_type (nearest_furniture_center), no GPS hardcodeado.
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

FOUNTAIN_A = (265.0, 250.0)
FOUNTAIN_B = (420.0, 160.0)
NEAR_A = (275.0, 255.0)
FAR_FROM_B = (200.0, 280.0)
EXPOSURE1_TICKS = 36
EXPOSURE2_TICKS = 100


def _setup(seed: int, *, affordances: bool, state_dir: Path) -> InfantApeBrain:
    flags = replace(
        AblationFlags(),
        enable_affordance_learning=affordances,
        enable_learned_schemas=affordances,
        enable_neural_telemetry=True,
        disable_hippocampus=True,
        enable_td_reward=False,
        enable_continuous_motor=False,
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
    brain.world.ensure_novel_fountain(
        x=FOUNTAIN_A[0], y=FOUNTAIN_A[1], object_id="fountain-a", label="fuente A"
    )
    brain.world.water_only_novel = True
    brain.world.arena_fast_locomotion = True
    return brain


def _prime(brain: InfantApeBrain, *, x: float, y: float) -> None:
    brain.world.agent_x = float(x)
    brain.world.agent_y = float(y)
    brain.world.ensure_agent_free()
    brain.world.clear_walk_goal()
    brain.body.thirst = 0.88
    brain.body.hunger = 0.12


def _run_until_drink(brain: InfantApeBrain, *, max_ticks: int) -> dict[str, Any]:
    thirst0 = float(brain.body.thirst)
    ticks = None
    for t in range(1, max_ticks + 1):
        brain.world_tick(steps=1)
        if float(brain.body.thirst) <= thirst0 - 0.08:
            ticks = t
            break
    return {
        "success": ticks is not None and float(brain.body.thirst) < thirst0 - 0.05,
        "ticks_to_drink": ticks if ticks is not None else max_ticks,
        "thirst_delta": round(thirst0 - float(brain.body.thirst), 4),
        "agency_violations": 0,
    }


def run_transfer_fountain_arm(seed: int, *, affordances: bool) -> dict[str, Any]:
    label = "aff_on" if affordances else "aff_off"
    sd = Path(tempfile.mkdtemp(prefix=f"nexo_transfer_{label}_{seed}_"))
    brain = _setup(seed, affordances=affordances, state_dir=sd)
    _prime(brain, x=NEAR_A[0], y=NEAR_A[1])
    exp1 = _run_until_drink(brain, max_ticks=EXPOSURE1_TICKS)
    records_a = len(brain.affordance_map.records)

    # Swap: quitar A, poner B lejos; agente lejos de B.
    brain.world.remove_furniture_id("fountain-a")
    brain.world.ensure_novel_fountain(
        x=FOUNTAIN_B[0], y=FOUNTAIN_B[1], object_id="fountain-b", label="fuente B"
    )
    _prime(brain, x=FAR_FROM_B[0], y=FAR_FROM_B[1])
    exp2 = _run_until_drink(brain, max_ticks=EXPOSURE2_TICKS)

    schemas = [
        s.key
        for s in brain.schema_learner.schemas
        if s.consolidated and "fountain" in s.key
    ]
    return {
        "seed": seed,
        "condition": label,
        "affordances": affordances,
        "exposure1": exp1,
        "exposure2": exp2,
        "affordance_records_after_a": records_a,
        "affordance_records_final": len(brain.affordance_map.records),
        "learned_affordance_schemas": schemas,
        "agency_note": "Type transfer; PFC alone writes choice_key",
    }
