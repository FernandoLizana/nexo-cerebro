"""
Arena: fuente seca — aprende el fallo (no alivia sed).

Tras varios intentos, AffordanceMap registra fallos; sueño puede podar
registros crónicamente inútiles. No escribe choice_key.
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

FOUNTAIN_XY = (72.0, 190.0)
NEAR_XY = (80.0, 195.0)


def _setup(seed: int, state_dir: Path) -> InfantApeBrain:
    flags = replace(
        AblationFlags(),
        enable_affordance_learning=True,
        enable_neural_telemetry=True,
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
        x=FOUNTAIN_XY[0], y=FOUNTAIN_XY[1], object_id="dry-fountain", label="fuente seca"
    )
    brain.world.water_only_novel = True
    brain.world.fountain_is_dry = True
    brain.world.arena_fast_locomotion = True
    return brain


def run_dry_fountain_failure(seed: int = 0, *, attempts: int = 4) -> dict[str, Any]:
    sd = Path(tempfile.mkdtemp(prefix=f"nexo_arena_dry_{seed}_"))
    brain = _setup(seed, sd)
    brain.world.agent_x = float(NEAR_XY[0])
    brain.world.agent_y = float(NEAR_XY[1])
    brain.world.ensure_agent_free()
    brain.body.thirst = 0.92
    brain.body.hunger = 0.1
    thirst0 = float(brain.body.thirst)
    choice_before = brain.deliberation.last.choice_key

    drink_events = 0
    for _ in range(attempts):
        ev = brain.world._interact({"seek_water": 0.95, "seek_food": 0.05})
        if not ev or ev.get("type") != "drink":
            continue
        drink_events += 1
        brain.agent_loop._handle_world_event_with_affordance(
            brain,
            event=ev,
            last_ep=None,
            drives={"seek_water": 0.95},
            decision_key=choice_before,
        )

    records = [
        r
        for r in brain.affordance_map.records.values()
        if r.object_type == "fountain" and r.candidate_key == "drink"
    ]
    record = records[0] if records else None
    sleep_stats = brain.affordance_map.consolidate_during_sleep()
    # Más intentos fallidos para forzar poda en el test de sueño.
    if record and record.observation_count < 3:
        for _ in range(3 - record.observation_count):
            before = {
                "hunger": 0.1,
                "thirst": 0.9,
                "fatigue": 0.2,
                "comfort": 0.5,
                "bladder": 0.1,
                "hygiene": 0.2,
                "pain": 0.0,
                "pleasure": 0.1,
            }
            after = dict(before)
            after["comfort"] = 0.48
            brain.affordance_map.observe(
                event={
                    "type": "drink",
                    "object_type": "fountain",
                    "object_id": "dry-fountain",
                    "target": "fuente seca",
                    "dry": True,
                },
                before=before,
                after=after,
                dominant_drive="seek_water",
                room="jardín",
                decision_key=choice_before,
            )
        sleep_stats = brain.affordance_map.consolidate_during_sleep()

    remaining = [
        r
        for r in brain.affordance_map.records.values()
        if r.object_id == "dry-fountain"
    ]
    return {
        "seed": seed,
        "drink_events": drink_events,
        "thirst_delta": round(thirst0 - float(brain.body.thirst), 4),
        "failure_count": int(record.failure_count) if record else 0,
        "success_count": int(record.success_count) if record else 0,
        "mean_gain": round(float(record.mean_homeostasis_gain), 4) if record else 0.0,
        "sleep": sleep_stats,
        "remaining_dry_records": len(remaining),
        "choice_unchanged": brain.deliberation.last.choice_key == choice_before,
        "agency_note": "Dry fountain fails; PFC alone writes choice_key",
    }
