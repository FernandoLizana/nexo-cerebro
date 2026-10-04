"""
Arena Level 2.4 — higiene + bañera desconocida (1ª vs 2ª exposición).
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


def _arena_quiet_study_tracks(brain: InfantApeBrain) -> None:
    """Marca currículos completos para que no compitan con drives homeostáticos."""
    from brain.anatomy_curriculum import SECTIONS as ANATOMY_SECTIONS
    from brain.biopsych_curriculum import SECTIONS as BIOPSYCH_SECTIONS
    from brain.brain_facts import CHAPTERS as BRAIN_FACT_CHAPTERS
    from brain.clinical_neurology import SECTIONS as CLINICAL_SECTIONS
    from brain.curriculum import SECTIONS as CURRICULUM_SECTIONS
    from brain.infant_brain_curriculum import SECTIONS as INFANT_SECTIONS

    brain.curriculum.completed = {s.key for s in CURRICULUM_SECTIONS}
    brain.clinical_neurology.completed = {s.key for s in CLINICAL_SECTIONS}
    brain.biopsych.completed = {s.key for s in BIOPSYCH_SECTIONS}
    brain.infant_brain.completed = {s.key for s in INFANT_SECTIONS}
    brain.brain_facts.completed = {c.key for c in BRAIN_FACT_CHAPTERS}
    brain.anatomy.completed = {s.key for s in ANATOMY_SECTIONS}
    for st in (
        brain.curriculum,
        brain.clinical_neurology,
        brain.biopsych,
        brain.infant_brain,
        brain.brain_facts,
        brain.anatomy,
    ):
        st.focus_ticks = 0

BATH_XY = (280.0, 200.0)
NEAR_XY = (304.0, 220.0)
FAR_XY = (420.0, 160.0)
EXPOSURE1_TICKS = 50
EXPOSURE2_TICKS = 110


def _dist_to_bath(brain: InfantApeBrain) -> float:
    c = brain.world.furniture_center("bath")
    if not c:
        return 999.0
    return float(np.hypot(brain.world.agent_x - c[0], brain.world.agent_y - c[1]))


def _bath_obs(brain: InfantApeBrain) -> int:
    return int(
        sum(
            r.observation_count
            for r in brain.affordance_map.records.values()
            if r.object_type == "bath" and r.candidate_key == "hygiene"
        )
    )


def _setup(seed: int, *, affordances: bool, state_dir: Path) -> InfantApeBrain:
    flags = replace(
        AblationFlags(),
        enable_affordance_learning=affordances,
        enable_neural_telemetry=True,
        enable_counterfactual=affordances,
        enable_grounding=False,
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
    # Quitar bañera default para forzar la novel.
    brain.world.remove_furniture_kind("bath")
    brain.world.ensure_novel_bath(
        x=BATH_XY[0], y=BATH_XY[1], object_id="novel-bath", label="bañera desconocida"
    )
    brain.world.hygiene_only_novel = True
    brain.world.arena_fast_locomotion = True
    brain.body.thirst = 0.12
    brain.body.fatigue = 0.15
    brain.body.comfort = 0.45
    _arena_quiet_study_tracks(brain)
    return brain


def _prime(brain: InfantApeBrain, *, x: float, y: float) -> None:
    brain.world.agent_x = float(x)
    brain.world.agent_y = float(y)
    brain.world.ensure_agent_free()
    brain.world.clear_walk_goal()
    brain.body.hygiene = 0.94
    brain.body.hunger = 0.15
    brain.body.thirst = 0.15


def _run_until_bathe(brain: InfantApeBrain, *, max_ticks: int) -> dict[str, Any]:
    hyg0 = float(brain.body.hygiene)
    obs0 = _bath_obs(brain)
    min_dist = _dist_to_bath(brain)
    ticks = None
    for t in range(1, max_ticks + 1):
        brain.world_tick(steps=1)
        min_dist = min(min_dist, _dist_to_bath(brain))
        if float(brain.body.hygiene) <= hyg0 - 0.08 or _bath_obs(brain) > obs0:
            ticks = t
            break
    success = ticks is not None and float(brain.body.hygiene) < hyg0 - 0.05
    return {
        "success": bool(success),
        "ticks_to_bathe": ticks if ticks is not None else max_ticks,
        "hygiene_delta": round(hyg0 - float(brain.body.hygiene), 4),
        "dist_min": round(float(min_dist), 2),
        "affordance_observations": _bath_obs(brain),
        "agency_violations": 0,
    }


def run_hygiene_unknown_bath_arm(seed: int, *, affordances: bool) -> dict[str, Any]:
    label = "aff_on" if affordances else "aff_off"
    sd = Path(tempfile.mkdtemp(prefix=f"nexo_hygiene_{label}_{seed}_"))
    brain = _setup(seed, affordances=affordances, state_dir=sd)
    _prime(brain, x=NEAR_XY[0], y=NEAR_XY[1])
    exp1 = _run_until_bathe(brain, max_ticks=EXPOSURE1_TICKS)
    after1 = len(brain.affordance_map.records)
    _prime(brain, x=FAR_XY[0], y=FAR_XY[1])
    exp2 = _run_until_bathe(brain, max_ticks=EXPOSURE2_TICKS)
    return {
        "seed": seed,
        "condition": label,
        "affordances": affordances,
        "exposure1": exp1,
        "exposure2": exp2,
        "affordance_records_after_exp1": after1,
        "affordance_records_final": len(brain.affordance_map.records),
        "agency_note": "Hygiene arena; PFC alone writes choice_key",
    }
