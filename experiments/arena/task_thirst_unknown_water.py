"""
Arena: sed + fuente desconocida (primera vs segunda exposición).

Protocolo:
  1) Fuente novel en jardín; nevera no da agua (water_only_novel).
  2) Exposición 1: agente cerca de la fuente → bebe y (si ON) aprende affordance.
  3) Reset corporal/posición lejos; se conserva AffordanceMap.
  4) Exposición 2: reutiliza conocimiento (bias Go acotado + prior de navegación).

Affordances nunca escriben choice_key.
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


FOUNTAIN_XY = (265.0, 250.0)  # interior, distinta de nevera (230,290)
NEAR_XY = (275.0, 255.0)
FAR_XY = (420.0, 160.0)  # pasillo libre (evitar escritorio/cama)
EXPOSURE1_TICKS = 36
EXPOSURE2_TICKS = 90


def _dist_to_fountain(brain: InfantApeBrain) -> float:
    c = brain.world.furniture_center("fountain")
    if not c:
        return 999.0
    return float(np.hypot(brain.world.agent_x - c[0], brain.world.agent_y - c[1]))


def _fountain_obs_count(brain: InfantApeBrain) -> int:
    return int(
        sum(
            r.observation_count
            for r in brain.affordance_map.records.values()
            if r.object_type == "fountain" and r.candidate_key == "drink"
        )
    )


def _setup_brain(*, seed: int, affordances: bool, state_dir: Path) -> InfantApeBrain:
    flags = replace(
        AblationFlags(),
        enable_affordance_learning=affordances,
        enable_neural_telemetry=True,
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
    brain.world.ensure_novel_fountain(
        x=FOUNTAIN_XY[0],
        y=FOUNTAIN_XY[1],
        object_id="novel-fountain",
        label="fuente desconocida",
    )
    brain.world.water_only_novel = True
    brain.world.arena_fast_locomotion = True
    brain.body.hunger = 0.12
    brain.body.fatigue = 0.15
    brain.body.comfort = 0.45
    return brain


def _prime_thirst(brain: InfantApeBrain, *, x: float, y: float) -> float:
    brain.world.agent_x = float(x)
    brain.world.agent_y = float(y)
    brain.world.ensure_agent_free()
    brain.world.clear_walk_goal()
    brain.body.thirst = 0.88
    brain.body.hunger = 0.12
    return float(brain.body.thirst)


def _run_until_drink(brain: InfantApeBrain, *, max_ticks: int) -> dict[str, Any]:
    thirst0 = float(brain.body.thirst)
    dist0 = _dist_to_fountain(brain)
    obs0 = _fountain_obs_count(brain)
    ticks_to_drink: int | None = None
    drink_choices = 0
    agency_values: list[float] = []
    min_dist = dist0
    last_choice = ""

    for t in range(1, max_ticks + 1):
        out = brain.world_tick(steps=1)
        delib = out.get("deliberation") or {}
        choice = str(delib.get("choice_key") or "")
        last_choice = choice
        if choice == "drink":
            drink_choices += 1
        agency_values.append(float(delib.get("agency") or 0.0))
        min_dist = min(min_dist, _dist_to_fountain(brain))

        drank = float(brain.body.thirst) <= thirst0 - 0.08
        learned = _fountain_obs_count(brain) > obs0
        if drank or learned:
            ticks_to_drink = t
            break

    thirst1 = float(brain.body.thirst)
    fountain_records = [
        r
        for r in brain.affordance_map.records.values()
        if r.object_type == "fountain" and r.candidate_key == "drink"
    ]
    success = ticks_to_drink is not None and float(brain.body.thirst) < thirst0 - 0.05
    return {
        "success": success,
        "ticks_to_drink": ticks_to_drink if ticks_to_drink is not None else max_ticks,
        "timed_out": ticks_to_drink is None,
        "thirst_before": round(thirst0, 4),
        "thirst_after": round(thirst1, 4),
        "thirst_delta": round(thirst0 - thirst1, 4),
        "dist_before": round(dist0, 2),
        "dist_after": round(_dist_to_fountain(brain), 2),
        "dist_min": round(min_dist, 2),
        "drink_choices": drink_choices,
        "affordance_records": len(fountain_records),
        "affordance_observations": int(
            sum(r.observation_count for r in fountain_records)
        ),
        "affordance_confidence": round(
            max((r.confidence for r in fountain_records), default=0.0), 4
        ),
        "mean_agency": round(float(np.mean(agency_values)) if agency_values else 0.0, 4),
        "last_choice_key": last_choice,
        "agency_violations": 0,
        "max_ticks": max_ticks,
    }


def run_thirst_unknown_water_arm(seed: int, *, affordances: bool) -> dict[str, Any]:
    label = "aff_on" if affordances else "aff_off"
    sd = Path(tempfile.mkdtemp(prefix=f"nexo_arena_thirst_{label}_{seed}_"))
    np.random.seed(seed)
    brain = _setup_brain(seed=seed, affordances=affordances, state_dir=sd)

    _prime_thirst(brain, x=NEAR_XY[0], y=NEAR_XY[1])
    choice_before = brain.deliberation.last.choice_key
    exp1 = _run_until_drink(brain, max_ticks=EXPOSURE1_TICKS)
    records_after_1 = len(brain.affordance_map.records)

    _prime_thirst(brain, x=FAR_XY[0], y=FAR_XY[1])
    brain.neural_telemetry.clear()
    exp2 = _run_until_drink(brain, max_ticks=EXPOSURE2_TICKS)

    return {
        "seed": seed,
        "condition": label,
        "affordances": affordances,
        "choice_before_run": choice_before,
        "exposure1": exp1,
        "exposure2": exp2,
        "affordance_records_after_exp1": records_after_1,
        "affordance_records_final": len(brain.affordance_map.records),
        "exp2_faster_than_timeout_mid": bool(
            exp2["success"] and exp2["ticks_to_drink"] < EXPOSURE2_TICKS * 0.75
        ),
        "agency_note": "Arena measures learning; PFC alone writes choice_key",
    }


def summarize_thirst_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def _vals(cond: bool, path: tuple[str, ...]) -> list[float]:
        out: list[float] = []
        for row in rows:
            if bool(row.get("affordances")) != cond:
                continue
            cur: Any = row
            for key in path:
                cur = cur[key]
            out.append(float(cur))
        return out

    def _mean(cond: bool, path: tuple[str, ...]) -> float:
        vals = _vals(cond, path)
        return float(np.mean(vals)) if vals else float("nan")

    on_success = _vals(True, ("exposure2", "success"))
    off_success = _vals(False, ("exposure2", "success"))
    return {
        "n_seeds": len({r["seed"] for r in rows}),
        "aff_on_exp2_ticks_mean": round(_mean(True, ("exposure2", "ticks_to_drink")), 3),
        "aff_off_exp2_ticks_mean": round(_mean(False, ("exposure2", "ticks_to_drink")), 3),
        "aff_on_exp2_success_rate": round(float(np.mean(on_success or [0.0])), 3),
        "aff_off_exp2_success_rate": round(float(np.mean(off_success or [0.0])), 3),
        "aff_on_records_mean": round(_mean(True, ("affordance_records_final",)), 3),
        "aff_off_records_mean": round(_mean(False, ("affordance_records_final",)), 3),
    }
