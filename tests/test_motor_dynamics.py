"""Bloque I — motor, cuerpo y mundo encarnado (items 85–92)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from brain.deliberation import ActionContestant
from brain.experiment_flags import AblationFlags
from brain.motor_dynamics import EmbodiedMotorStack
from brain.somatic_affordances import CONTACT_EFFECTS


def test_continuous_motor_bind():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_motor_dynamics=True,
        enable_continuous_motor=True,
    )
    stack = EmbodiedMotorStack()
    stack.bind_continuous_motor(brain)
    assert brain.motor_policy.alpha >= 0.22


def test_cerebellum_adaptation():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_motor_dynamics=True,
        enable_cerebellum_adaptation=True,
    )
    stack = EmbodiedMotorStack()
    out = stack.cerebellum_adapt(brain, planned=[1, 4], executed=[1, 2])
    assert isinstance(out, list)
    assert stack.cerebellum_error >= 0.0


def test_basal_habituation_boosts_go():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_motor_dynamics=True,
        enable_basal_habituation=True,
    )
    brain.deliberation.last.choice_key = "drink"
    stack = EmbodiedMotorStack()
    stack.action_counts["drink"] = 4
    c = ActionContestant(key="drink", label="beber", drive="seek_water", limbic=0.3, pfc=0.2, habit=0.1, go=0.2)
    go_before = c.go
    stack.basal_habituation(brain, [c])
    assert c.go > go_before


def test_muscular_fatigue_coupling():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_motor_dynamics=True,
        enable_muscular_fatigue=True,
        enable_circadian=True,
    )
    brain.biomech.physical_fatigue = 0.3
    stack = EmbodiedMotorStack()
    out = stack.couple_fatigue_circadian(brain)
    assert "physical_fatigue" in out


def test_world_depth_sync():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_motor_dynamics=True,
        enable_world_depth=True,
    )
    brain.biomech.height = 0.12
    stack = EmbodiedMotorStack()
    z = stack.update_world_depth(brain)
    assert z == pytest.approx(0.12)
    assert brain.world.agent_z == pytest.approx(0.12)


def test_somatic_passive_contacts():
    assert "tv" in CONTACT_EFFECTS
    assert "stove" in CONTACT_EFFECTS


def test_food_cycle_tick():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_motor_dynamics=True,
        enable_food_cycle=True,
    )
    stack = EmbodiedMotorStack()
    out = stack.tick_food_cycle(brain)
    assert "pantry_raw" in out
    assert stack.food_ticks == 1


def test_desk_study_deterministic():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_motor_dynamics=True,
        enable_desk_study_deterministic=True,
    )
    stack = EmbodiedMotorStack()
    ev = stack.resolve_desk_study(brain, choice_key="study", curiosity=0.5)
    assert ev.get("type") in (
        "curriculum_study",
        "brain_facts_study",
        "anatomy_study",
        "clinical_study",
        "biopsych_study",
        "infant_study",
        "library_study",
        "web_search",
    )
