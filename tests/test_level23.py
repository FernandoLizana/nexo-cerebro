"""Level 2.3 — HUD causal, contrafactual, sueño, arenas extra, demo-lite."""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

from brain.affordance_map import AffordanceMap
from brain.causal_hud import build_causal_hud
from brain.counterfactual_simulator import COUNTERFACTUAL_BIAS_MAX, CounterfactualSimulator
from brain.dialogue_engine import is_meta_assistant_speech
from brain.experiment_flags import AblationFlags
from brain.language_cortex import LanguageContext, LanguageCortex
from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE, DEMO_LITE_PROFILE, resolve_default_profile
from experiments.arena.task_dry_fountain import run_dry_fountain_failure
from experiments.arena.task_hunger_unknown_bowl import run_hunger_unknown_bowl_arm


def test_causal_hud_read_only():
    sd = Path(tempfile.mkdtemp(prefix="nexo_hud_"))
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
        experiment_flags=AblationFlags(),
    )
    choice_before = brain.deliberation.last.choice_key
    hud = build_causal_hud(brain)
    assert "one_liner" in hud
    assert hud["agency_guard"]["hud_selects_actions"] is False
    assert hud["agency_guard"]["deliberation_selects_actions"] is True
    assert brain.deliberation.last.choice_key == choice_before


def test_counterfactual_bias_bounded_and_agency_safe():
    sim = CounterfactualSimulator()
    preds = sim.predict_for(
        candidate_keys=["drink", "eat", "wander"],
        dominant_drive="seek_water",
        room="jardín",
    )
    assert preds
    biases = sim.biases_for(
        candidate_keys=["drink", "eat", "wander"],
        dominant_drive="seek_water",
        room="jardín",
    )
    assert "drink" in biases
    assert abs(biases["drink"]) <= COUNTERFACTUAL_BIAS_MAX + 1e-9


def test_affordance_sleep_prunes_chronic_failures():
    am = AffordanceMap()
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
    for _ in range(3):
        am.observe(
            event={
                "type": "drink",
                "object_type": "fountain",
                "object_id": "dry-x",
                "target": "seca",
            },
            before=before,
            after=after,
            dominant_drive="seek_water",
            room="jardín",
        )
    assert len(am.records) == 1
    rec = next(iter(am.records.values()))
    assert rec.failure_count >= 3
    assert rec.confidence < 0.18
    stats = am.consolidate_during_sleep()
    assert stats["pruned"] >= 1
    assert len(am.records) == 0


def test_demo_lite_profile_env(monkeypatch):
    monkeypatch.setenv("CEREBRO_DEMO_LITE", "1")
    assert resolve_default_profile() is DEMO_LITE_PROFILE


def test_meta_filter_and_drive_fallback():
    assert is_meta_assistant_speech("No puedo cumplir con esa solicitud.")
    assert is_meta_assistant_speech("Analizando el estado proporcionado…")
    cortex = LanguageCortex()
    ctx = LanguageContext(body={"thirst": 0.8, "hunger": 0.1}, drives={"seek_water": 0.7})
    line = cortex._minimal_fallback(ctx)
    assert "sed" in line.lower() or "agua" in line.lower()


def test_novel_bowl_eat_and_affordance():
    sd = Path(tempfile.mkdtemp(prefix="nexo_bowl_"))
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
    fu = brain.world.ensure_novel_food_bowl()
    brain.world.food_only_novel = True
    brain.world.agent_x = fu.x + fu.w / 2
    brain.world.agent_y = fu.y + fu.h / 2
    brain.body.hunger = 0.9
    brain.body.thirst = 0.1
    choice_before = brain.deliberation.last.choice_key
    ev = brain.world._interact({"seek_food": 0.9, "seek_water": 0.05})
    assert ev is not None
    assert ev["type"] == "eat"
    assert ev["object_type"] == "food_bowl"
    brain.agent_loop._handle_world_event_with_affordance(
        brain,
        event=ev,
        last_ep=None,
        drives={"seek_food": 0.9},
        decision_key=choice_before,
    )
    assert brain.body.hunger < 0.55
    assert any(r.object_type == "food_bowl" for r in brain.affordance_map.records.values())
    assert brain.deliberation.last.choice_key == choice_before


def test_dry_fountain_learns_failure():
    row = run_dry_fountain_failure(0, attempts=3)
    assert row["drink_events"] >= 1
    assert row["thirst_delta"] < 0.08
    assert row["failure_count"] >= 1
    assert row["mean_gain"] < 0.015
    assert row["choice_unchanged"]


def test_hunger_arena_smoke_aff_on():
    on = run_hunger_unknown_bowl_arm(0, affordances=True)
    off = run_hunger_unknown_bowl_arm(0, affordances=False)
    assert on["exposure1"]["success"]
    assert on["affordance_records_after_exp1"] >= 1
    assert on["exposure2"]["success"]
    assert not off["exposure2"]["success"]
    assert on["exposure2"]["ticks_to_eat"] < off["exposure2"]["ticks_to_eat"]
