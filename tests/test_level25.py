"""Level 2.5 — discriminación bueno/malo + regresión navegación."""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

from brain.experiment_flags import AblationFlags
from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE
from experiments.arena.task_discrimination import run_discrimination_good_vs_dry
from experiments.arena.task_transfer_fountain import run_transfer_fountain_arm


def test_per_object_dry_flag():
    sd = Path(tempfile.mkdtemp(prefix="nexo_dry_id_"))
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
        experiment_flags=AblationFlags(),
    )
    good = brain.world.ensure_novel_fountain(x=100, y=100, object_id="g")
    dry = brain.world.ensure_novel_fountain(x=200, y=200, object_id="d")
    brain.world.dry_object_ids.add("d")
    assert not brain.world.is_object_dry("g")
    assert brain.world.is_object_dry("d")
    brain.world.agent_x, brain.world.agent_y = dry.x + 8, dry.y + 8
    ev = brain.world._interact({"seek_water": 0.9})
    assert ev and ev["object_id"] == "d" and ev["dry"] is True
    brain.world.agent_x, brain.world.agent_y = good.x + 8, good.y + 8
    ev2 = brain.world._interact({"seek_water": 0.9})
    assert ev2 and ev2["object_id"] == "g" and ev2["dry"] is False


def test_discrimination_aff_on_prefers_good():
    on = run_discrimination_good_vs_dry(0, affordances=True)
    off = run_discrimination_good_vs_dry(0, affordances=False)
    assert "fountain-good" in on["records"]
    assert "fountain-dry" in on["records"]
    assert on["records"]["fountain-good"]["gain"] > on["records"]["fountain-dry"]["gain"]
    assert on["goal_is_good"]
    assert on["drank_success"]
    # Sin affordances: no hay prior al bueno; no debe marcar goal_is_good.
    assert not off["goal_is_good"]
    assert on["ticks"] <= off["ticks"]


def test_transfer_still_works_after_discrimination_nav_fix():
    on = run_transfer_fountain_arm(0, affordances=True)
    assert on["exposure1"]["success"]
    assert on["exposure2"]["success"]
