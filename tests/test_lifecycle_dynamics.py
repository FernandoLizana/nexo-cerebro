"""Bloque J — sueño, desarrollo y ciclo vital (items 93–97)."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

import pytest

from brain.deliberation import ActionContestant
from brain.experiment_flags import AblationFlags
from brain.lifecycle_dynamics import LifecycleDynamicsStack


def test_full_sleep_cycle_builds_timeline():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_lifecycle_dynamics=True,
        enable_full_sleep_architecture=True,
        enable_selective_sleep=True,
    )
    stack = LifecycleDynamicsStack()
    fake_sleep = {
        "slept": True,
        "replays": 3,
        "swr_bursts": 2,
        "replay_mode": "selective",
        "sleep_phases": [
            {"cycle": 1, "phase": "nrem_light", "replays": 1, "swr": 1, "consolidated": 0},
            {"cycle": 1, "phase": "rem", "replays": 2, "swr": 1, "consolidated": 1},
        ],
    }
    with patch.object(brain, "sleep", return_value=fake_sleep):
        out = stack.run_full_sleep_cycle(brain, cycles=1)
    assert out.get("slept") is True
    assert len(stack.sleep_timeline) == 2
    assert stack.last_sleep_summary.get("phases") == 2


def test_maybe_trigger_sleep_requires_rest_and_night():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_lifecycle_dynamics=True,
        enable_full_sleep_architecture=True,
    )
    brain.deliberation.last.choice_key = "explore"
    stack = LifecycleDynamicsStack()
    assert stack.maybe_trigger_sleep(brain, hour=23, sleep_need=0.8) is None
    brain.deliberation.last.choice_key = "rest"
    fake_sleep = {"slept": True, "sleep_phases": [{"cycle": 1, "phase": "rem", "replays": 1}]}
    with patch.object(brain, "sleep", return_value=fake_sleep):
        triggered = stack.maybe_trigger_sleep(brain, hour=23, sleep_need=0.8)
    assert triggered is not None
    assert triggered.get("slept") is True


def test_nocturnal_study_weights():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_lifecycle_dynamics=True,
        enable_nocturnal_study=True,
        enable_sleep_study=True,
    )
    stack = LifecycleDynamicsStack()
    out = stack.tick_nocturnal_study(brain, phase="rem")
    assert "weights" in out
    assert stack.nocturnal_sessions >= 1


def test_lifecycle_stages_plasticity():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_lifecycle_dynamics=True,
        enable_lifecycle_stages=True,
        enable_lifecycle_plasticity=True,
    )
    brain.lifecycle.age_ticks = 0
    stack = LifecycleDynamicsStack()
    neuro = stack.apply_lifecycle_stages(brain)
    assert brain.lifecycle.stage == "infante"
    assert neuro.get("plasticity_scale", 0) > 1.0
    assert brain.cortex.plasticity_mult > brain.profile.plasticity_mult


def test_puberty_hormones_adolescent_only():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_lifecycle_dynamics=True,
        enable_puberty_hormones=True,
    )
    brain.lifecycle.age_ticks = brain.lifecycle.ticks_per_year * 20
    brain.lifecycle._update_stage()
    assert brain.lifecycle.stage == "adulto"
    stack = LifecycleDynamicsStack()
    assert stack.apply_puberty_hormones(brain) == {}

    brain.lifecycle.age_ticks = brain.lifecycle.ticks_per_year * 14
    brain.lifecycle._update_stage()
    assert brain.lifecycle.stage == "adolescente"
    pub = stack.apply_puberty_hormones(brain)
    assert pub.get("stage") == "adolescente"
    assert pub.get("pfc_inhibition_scale", 1) < 0.75


def test_cognitive_aging_wm_and_recall():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_lifecycle_dynamics=True,
        enable_cognitive_aging=True,
        enable_limited_wm=True,
        enable_memory_dynamics=True,
    )
    brain.working_memory.limited = True
    brain.lifecycle.age_ticks = int(brain.lifecycle.ticks_per_year * 60)
    brain.lifecycle._update_stage()
    assert brain.lifecycle.stage == "anciano"
    stack = LifecycleDynamicsStack()
    aging = stack.apply_cognitive_aging(brain)
    assert aging["wm_capacity"] <= 5
    assert stack.recall_aging_penalty >= 0.08
    assert stack.pfc_compensation > 0


def test_deliberation_aging_boost():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    stack = LifecycleDynamicsStack()
    stack.pfc_compensation = 0.12
    c_low = ActionContestant(key="rest", label="descansar", drive="", limbic=0.2, pfc=0.15, habit=0, go=0.2)
    c_high = ActionContestant(key="study", label="estudiar", drive="", limbic=0.2, pfc=0.55, habit=0, go=0.3)
    pfc_before = c_high.pfc
    assert stack.deliberation_aging_boost(brain, [c_low, c_high]) is True
    assert c_high.pfc > pfc_before


def test_post_tick_integration():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_lifecycle_dynamics=True,
        enable_lifecycle_stages=True,
        enable_puberty_hormones=True,
        enable_cognitive_aging=False,
        enable_nocturnal_study=True,
        enable_sleep_study=True,
    )
    brain.lifecycle.age_ticks = brain.lifecycle.ticks_per_year * 14
    brain.lifecycle._update_stage()
    stack = LifecycleDynamicsStack()
    metrics = stack.post_tick(brain, hour=23, sleep_need=0.3, sleep_phase="awake")
    assert "neuro" in metrics
    assert "puberty" in metrics
    assert "nocturnal_study" in metrics
    assert "sleep_triggered" not in metrics


def test_recall_penalty_in_memory_dynamics():
    from brain import InfantApeBrain
    from brain.memory_dynamics import MemoryDynamicsStack
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_lifecycle_dynamics=True,
        enable_cognitive_aging=True,
        enable_memory_dynamics=True,
    )
    brain.lifecycle_dynamics.recall_aging_penalty = 0.15
    mem = {"key": "k1", "valence": 0.2, "arousal": 0.3, "updated_at": 0}
    stack = MemoryDynamicsStack()
    base = stack.adjust_recall_score(brain, mem, 0.8)
    brain.lifecycle_dynamics.recall_aging_penalty = 0.0
    higher = stack.adjust_recall_score(brain, mem, 0.8)
    assert base < higher


def test_to_dict_hud_fields():
    stack = LifecycleDynamicsStack()
    stack.sleep_timeline.append({"cycle": 1, "phase": "rem", "replays": 2})
    d = stack.to_dict()
    assert "sleep_timeline" in d
    assert d.get("agency_note")
