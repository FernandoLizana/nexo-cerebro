"""Bloque G — emoción, afecto y vínculo social (items 67–76)."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from brain.affect import AffectChemistry
from brain.affect_dynamics import (
    ATTACHMENT_ANXIOUS,
    ATTACHMENT_SECURE,
    AffectDynamicsStack,
    HPAAxis,
    receptor_panel,
)
from brain.experiment_flags import AblationFlags
from brain.goal_stack import GoalFrame, GoalStack


def test_receptor_panel_alpha_beta():
    aff = AffectChemistry()
    aff.dopamine.release(0.4)
    aff.dopamine.step()
    panel = receptor_panel(aff)
    assert "alpha" in panel and "beta" in panel
    assert 0 <= panel["alpha"]["dopamine"] <= 1
    assert 0 <= panel["beta"]["dopamine"] <= 1


def test_hpa_axis_cascade():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(AblationFlags(), enable_affect_dynamics=True, enable_hpa_axis=True)
    hpa = HPAAxis()
    before = brain.affect.cortisol.bound
    out = hpa.step(brain, stress=0.7)
    assert out["crh"] > 0.15
    assert out["acth"] > 0.15
    assert brain.affect.cortisol.bound >= before


def test_pfc_amygdala_fear_inhibition():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_affect_dynamics=True,
        enable_emotion_regulation=True,
    )
    brain.amygdala.arousal = 0.6
    brain.persona.attachment = 0.6
    stack = AffectDynamicsStack(safe_context_ticks=10)
    arousal_before = brain.amygdala.arousal
    stack.pfc_amygdala_regulation(brain)
    assert brain.amygdala.arousal <= arousal_before


def test_empathy_contagion_near_companion():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_affect_dynamics=True,
        enable_empathy_contagion=True,
    )
    brain.world.agent_x = 100.0
    brain.world.agent_y = 100.0
    brain.companion.x = 110.0
    brain.companion.y = 105.0
    stack = AffectDynamicsStack()
    contagion = stack.empathy_contagion_step(brain)
    assert contagion >= 0.0


def test_bowlby_attachment_styles():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_affect_dynamics=True,
        enable_attachment_style=True,
    )
    brain.persona.attachment = 0.6
    brain.affect.cortisol.bound = 0.3
    stack = AffectDynamicsStack()
    assert stack.bowlby_attachment_style(brain) == ATTACHMENT_SECURE
    brain.affect.cortisol.bound = 0.65
    assert stack.bowlby_attachment_style(brain) == ATTACHMENT_ANXIOUS


def test_social_shame_on_failure():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_affect_dynamics=True,
        enable_social_shame=True,
    )
    brain.chemistry.proximity = 0.7
    stack = AffectDynamicsStack()
    shame = stack.social_shame(brain, failed=True, witnessed=True)
    assert shame > 0.1


def test_liking_vs_wanting_split():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_affect_dynamics=True,
        enable_hedonic_wanting=True,
        enable_td_reward=True,
    )
    brain.hedonics.mu_opioid = 0.7
    brain.modulators.dopamine = 0.8
    brain.hedonics.craving = 0.6
    stack = AffectDynamicsStack()
    out = stack.split_liking_wanting(brain)
    assert out["liking"] > 0.4
    assert out["wanting"] > 0.4


def test_goal_frustration_and_stall():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_affect_dynamics=True,
        enable_goal_frustration=True,
    )
    gs = GoalStack()
    gs.frames.append(
        GoalFrame(choice_key="eat", label="comer", target="fridge", phase="navigate")
    )
    for _ in range(4):
        stall = gs.tick_stall(progressed=False)
    stack = AffectDynamicsStack()
    fr = stack.goal_frustration(brain, stall_ticks=stall)
    assert fr > 0.2


def test_persistent_mood_inertia():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_affect_dynamics=True,
        enable_persistent_mood=True,
    )
    brain.affect.dopamine.bound = 0.75
    brain.affect.serotonin.bound = 0.65
    stack = AffectDynamicsStack()
    mood = stack.update_mood_inertia(brain)
    assert mood in ("content", "excited", "curious", "calm", "stressed", "uneasy", "sleepy")
    assert brain.persona.mood == mood


def test_social_turn_state():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    stack = AffectDynamicsStack()
    st = stack.social_turn_state(brain)
    assert -1 <= st["valence"] <= 1
    assert 0 <= st["arousal"] <= 1
