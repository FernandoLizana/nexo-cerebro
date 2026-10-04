"""Level 2.4 — transferencia, schemas causales, higiene, física."""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

import pytest

from brain.experiment_flags import AblationFlags
from brain.learned_schemas import SchemaLearner
from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE
from experiments.arena.task_hygiene_unknown_bath import run_hygiene_unknown_bath_arm
from experiments.arena.task_physics_locomotion import run_physics_locomotion_smoke
from experiments.arena.task_transfer_fountain import run_transfer_fountain_arm


def test_nearest_furniture_and_multiple_fountains():
    sd = Path(tempfile.mkdtemp(prefix="nexo_multi_f_"))
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
        experiment_flags=AblationFlags(),
    )
    a = brain.world.ensure_novel_fountain(x=100, y=100, object_id="fa")
    b = brain.world.ensure_novel_fountain(x=400, y=300, object_id="fb")
    assert a.id != b.id
    brain.world.agent_x, brain.world.agent_y = 110, 110
    near = brain.world.nearest_furniture_center("fountain")
    assert near is not None
    assert abs(near[0] - (a.x + a.w / 2)) < 1.0


def test_schema_from_affordance_success():
    sl = SchemaLearner(consolidate_after=4)
    out = None
    for _ in range(3):
        created = sl.note_affordance_success(
            candidate_key="drink",
            object_type="fountain",
            dominant_drive="seek_water",
            room="jardín",
            homeostasis_gain=0.4,
        )
        if created is not None:
            out = created
    assert out is not None
    assert out.key.startswith("learned_aff_")
    assert out.parent_key == "drink"
    assert out.consolidated
    assert any(s.key == out.key for s in sl.schemas)


@pytest.mark.slow
def test_transfer_fountain_aff_on():
    on = run_transfer_fountain_arm(0, affordances=True)
    off = run_transfer_fountain_arm(0, affordances=False)
    assert on["exposure1"]["success"]
    assert on["affordance_records_after_a"] >= 1
    assert on["exposure2"]["success"]
    assert not off["exposure2"]["success"]
    assert on["exposure2"]["ticks_to_drink"] < off["exposure2"]["ticks_to_drink"]


@pytest.mark.slow
def test_hygiene_arena_smoke():
    on = run_hygiene_unknown_bath_arm(0, affordances=True)
    off = run_hygiene_unknown_bath_arm(0, affordances=False)
    assert on["exposure1"]["success"]
    assert on["affordance_records_after_exp1"] >= 1
    assert on["exposure2"]["success"]
    assert not off["exposure2"]["success"]


@pytest.mark.slow
def test_physics_locomotion_smoke():
    row = run_physics_locomotion_smoke(0)
    assert row["drank_near"]
    assert row["arena_fast_locomotion"] is False
    # Far path: success preferred; if timeout, at least se acercó.
    assert row["success_far"] or row["dist_final"] < 120.0
