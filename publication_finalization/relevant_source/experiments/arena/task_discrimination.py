"""
Arena Level 2.5 — discriminación: fuente buena vs fuente seca.

Ambas presentes. Tras experimentar ambas, con affordances el prior de
navegación debe preferir el object_id exitoso (no el más cercano seco).
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

GOOD_XY = (420.0, 160.0)  # lejos
DRY_XY = (280.0, 240.0)  # más cerca del spawn de test
SPAWN_XY = (300.0, 250.0)  # cerca de la seca → sin aprendizaje iría a la mala
NEAR_DRY = (288.0, 245.0)
NEAR_GOOD = (428.0, 165.0)
CHOICE_TICKS = 110


def _dist(brain: InfantApeBrain, object_id: str) -> float:
    fu = brain.world.furniture_by_id(object_id)
    if not fu:
        return 999.0
    return float(
        np.hypot(brain.world.agent_x - (fu.x + fu.w / 2), brain.world.agent_y - (fu.y + fu.h / 2))
    )


def _setup(seed: int, *, affordances: bool, state_dir: Path) -> InfantApeBrain:
    flags = replace(
        AblationFlags(),
        enable_affordance_learning=affordances,
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
        x=GOOD_XY[0], y=GOOD_XY[1], object_id="fountain-good", label="fuente buena"
    )
    brain.world.ensure_novel_fountain(
        x=DRY_XY[0], y=DRY_XY[1], object_id="fountain-dry", label="fuente seca"
    )
    brain.world.dry_object_ids.add("fountain-dry")
    brain.world.water_only_novel = True
    brain.world.arena_fast_locomotion = True
    return brain


def _force_drink(brain: InfantApeBrain, *, x: float, y: float, object_id: str) -> None:
    brain.world.agent_x = float(x)
    brain.world.agent_y = float(y)
    brain.world.ensure_agent_free()
    brain.body.thirst = 0.9
    brain.body.hunger = 0.1
    choice = brain.deliberation.last.choice_key
    for _ in range(3):
        ev = brain.world._interact({"seek_water": 0.95, "seek_food": 0.05})
        if not ev or ev.get("type") != "drink":
            continue
        # Forzar identidad del objeto bajo prueba.
        ev = {**ev, "object_id": object_id, "dry": brain.world.is_object_dry(object_id)}
        brain.agent_loop._handle_world_event_with_affordance(
            brain,
            event=ev,
            last_ep=None,
            drives={"seek_water": 0.95},
            decision_key=choice,
        )


def run_discrimination_good_vs_dry(seed: int, *, affordances: bool) -> dict[str, Any]:
    label = "aff_on" if affordances else "aff_off"
    sd = Path(tempfile.mkdtemp(prefix=f"nexo_discrim_{label}_{seed}_"))
    brain = _setup(seed, affordances=affordances, state_dir=sd)

    # Experiencia: primero seca (fallo), luego buena (éxito).
    _force_drink(brain, x=NEAR_DRY[0], y=NEAR_DRY[1], object_id="fountain-dry")
    _force_drink(brain, x=NEAR_GOOD[0], y=NEAR_GOOD[1], object_id="fountain-good")

    records = {
        r.object_id: {
            "gain": round(r.mean_homeostasis_gain, 4),
            "fail": r.failure_count,
            "ok": r.success_count,
            "conf": round(r.confidence, 4),
        }
        for r in brain.affordance_map.records.values()
        if r.candidate_key == "drink"
    }

    # Elección: spawn cerca de la seca; sed alta; sin GPS.
    brain.world.agent_x = float(SPAWN_XY[0])
    brain.world.agent_y = float(SPAWN_XY[1])
    brain.world.ensure_agent_free()
    brain.world.clear_walk_goal()
    brain.body.thirst = 0.92
    brain.body.hunger = 0.1
    thirst0 = float(brain.body.thirst)
    drank = False
    ticks = CHOICE_TICKS
    for t in range(1, CHOICE_TICKS + 1):
        brain.world_tick(steps=1)
        if float(brain.body.thirst) < thirst0 - 0.08:
            drank = True
            ticks = t
            break

    dist_good = _dist(brain, "fountain-good")
    dist_dry = _dist(brain, "fountain-dry")
    preferred_good = dist_good < dist_dry
    goal = brain.agent_loop._affordance_water_goal(brain)
    good_fu = brain.world.furniture_by_id("fountain-good")
    goal_is_good = False
    if goal and good_fu:
        gx, gy = good_fu.x + good_fu.w / 2, good_fu.y + good_fu.h / 2
        goal_is_good = abs(goal[0] - gx) < 8 and abs(goal[1] - gy) < 8

    return {
        "seed": seed,
        "condition": label,
        "affordances": affordances,
        "records": records,
        "drank_success": drank,
        "ticks": ticks,
        "thirst_delta": round(thirst0 - float(brain.body.thirst), 4),
        "dist_good": round(dist_good, 2),
        "dist_dry": round(dist_dry, 2),
        "preferred_good": preferred_good,
        "goal_is_good": goal_is_good,
        "agency_note": "Discrimination; PFC alone writes choice_key",
    }
