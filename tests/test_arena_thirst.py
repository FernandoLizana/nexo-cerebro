"""Level 2.2 — Arena thirst + fuente desconocida + telemetría."""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

import numpy as np

from brain.experiment_flags import AblationFlags
from brain.mind import InfantApeBrain
from brain.neural_telemetry import NeuralTelemetry
from brain.profile import COMPACT_PROFILE
from experiments.arena.task_thirst_unknown_water import (
    run_thirst_unknown_water_arm,
    summarize_thirst_rows,
)


def test_novel_fountain_drink_event_and_affordance():
    sd = Path(tempfile.mkdtemp(prefix="nexo_fountain_"))
    flags = replace(
        AblationFlags(),
        enable_affordance_learning=True,
        disable_hippocampus=True,
    )
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
        experiment_flags=flags,
    )
    brain.world.ensure_home()
    fu = brain.world.ensure_novel_fountain()
    brain.world.water_only_novel = True
    brain.world.agent_x = fu.x + fu.w / 2
    brain.world.agent_y = fu.y + fu.h / 2
    brain.body.thirst = 0.9
    brain.body.hunger = 0.1
    choice_before = brain.deliberation.last.choice_key

    ev = brain.world._interact({"seek_water": 0.9, "seek_food": 0.05})
    assert ev is not None
    assert ev["type"] == "drink"
    assert ev["object_type"] == "fountain"

    brain.agent_loop._handle_world_event_with_affordance(
        brain,
        event=ev,
        last_ep=None,
        drives={"seek_water": 0.9},
        decision_key=choice_before,
    )
    assert brain.body.thirst < 0.55
    assert len(brain.affordance_map.records) == 1
    record = next(iter(brain.affordance_map.records.values()))
    assert record.object_type == "fountain"
    assert record.candidate_key == "drink"
    assert brain.deliberation.last.choice_key == choice_before


def test_headless_applies_drink_consequences():
    sd = Path(tempfile.mkdtemp(prefix="nexo_headless_drink_"))
    flags = replace(
        AblationFlags(),
        enable_affordance_learning=True,
        disable_hippocampus=True,
    )
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
        experiment_flags=flags,
    )
    brain.world.ensure_home()
    fu = brain.world.ensure_novel_fountain()
    brain.world.water_only_novel = True
    brain.world.agent_x = fu.x + 8
    brain.world.agent_y = fu.y + 8
    brain.world.ensure_agent_free()
    brain.body.thirst = 0.9
    brain.body.hunger = 0.05
    thirst0 = float(brain.body.thirst)

    drank = False
    for _ in range(24):
        brain.world_tick(steps=1)
        if float(brain.body.thirst) < thirst0 - 0.08:
            drank = True
            break
    assert drank
    assert any(
        r.object_type == "fountain" for r in brain.affordance_map.records.values()
    )


def test_telemetry_records_without_selecting_actions():
    tel = NeuralTelemetry(capacity=8)
    choice_holder = {"choice_key": "wander"}
    tel.record_from_tick(
        {
            "deliberation": {"choice_key": "drink", "agency": 0.5},
            "drives": {"seek_water": 0.8},
            "world": {"room": "jardín"},
            "affordance_map": {"record_count": 1, "last_biases": {"drink": 0.05}},
            "events": [{"type": "drink", "object_type": "fountain"}],
        },
        tick=3,
    )
    assert choice_holder["choice_key"] == "wander"
    latest = tel.latest()
    assert latest is not None
    assert latest["choice_key"] == "drink"
    assert latest["top_drive"] == "seek_water"
    assert AblationFlags().enable_neural_telemetry is False


def test_arena_arm_smoke_aff_on_learns():
    on = run_thirst_unknown_water_arm(0, affordances=True)
    off = run_thirst_unknown_water_arm(0, affordances=False)
    assert on["exposure1"]["success"]
    assert on["affordance_records_after_exp1"] >= 1
    assert on["exposure2"]["success"]
    assert on["exposure2"]["agency_violations"] == 0
    # Sin affordances: no hay GPS a la fuente en exposición 2.
    assert not off["exposure2"]["success"]
    assert off["affordance_records_final"] == 0
    assert on["exposure2"]["ticks_to_drink"] < off["exposure2"]["ticks_to_drink"]
    summary = summarize_thirst_rows([on, off])
    assert summary["aff_on_exp2_success_rate"] == 1.0
    assert summary["aff_off_exp2_success_rate"] == 0.0
