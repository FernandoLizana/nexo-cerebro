"""Bloque D — atención, consciencia y cognición ejecutiva (items 33–44)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from brain.attention import AttentionBudget, competitive_filter
from brain.executive_cognition import (
    DefaultModeNetwork,
    DualTaskMonitor,
    ExecutiveCognitionStack,
    SetShiftingController,
    StroopController,
)
from brain.experiment_flags import AblationFlags
from brain.goal_stack import GoalStack, TOWER_PLANS


def test_attention_competitive_filter():
    percepts = [
        {"label": "dolor fuerte", "salience": 0.7, "kind": "pain"},
        {"label": "libro escritorio", "salience": 0.4, "kind": "book"},
    ]
    attended, ignored, st = competitive_filter(
        percepts,
        drives={"seek_curiosity": 0.6},
        goal="estudiar escritorio",
        budget=2,
    )
    assert len(attended) <= 2
    assert st.focus_label
    assert st.focus_source in ("bottom_up", "top_down", "mixed")


def test_tower_goal_stack():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(AblationFlags(), enable_tower_goals=True)
    stack = GoalStack()
    ok = stack.push_from_deliberation("study", "Estudiar", brain)
    assert ok
    assert stack.depth() == len(TOWER_PLANS["study"])
    assert stack.peek().phase == "navigate"


def test_stroop_inhibits_limbic():
    from brain.deliberation import ActionContestant

    stroop = StroopController()
    limbic = ActionContestant(key="eat", label="comer", drive="seek_food", limbic=0.7, pfc=0.1, go=0.8)
    pfc = ActionContestant(key="study", label="estudiar", drive="seek_curiosity", limbic=0.1, pfc=0.6, go=0.5)
    limbic.no_go = 0.1
    limbic.net = limbic.go - limbic.no_go
    stroop.apply([limbic, pfc], limbic_top=limbic, pfc_top=pfc, goal_key="study")
    assert stroop.stroop_active
    assert limbic.no_go > 0.1


def test_set_shifting_cost():
    ctrl = SetShiftingController()
    c1 = ctrl.note_choice("eat")
    c2 = ctrl.note_choice("study")
    assert c2 > c1


def test_dmn_replay_at_rest():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(AblationFlags(), enable_dmn_replay=True, enable_executive_cognition=True)
    dmn = DefaultModeNetwork()
    out = dmn.tick(brain, drives={"seek_rest": 0.1}, surprise=0.1)
    assert "active" in out


def test_cingulate_redeliberate_signal():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.deliberation.last.inhibited = True
    brain.deliberation.last.conflict = 0.55
    out = brain.cingulate.integrate(brain, surprise=0.85)
    assert out["should_redeliberate"] is True


def test_consciousness_global_workspace_hud():
    from brain.consciousness import ConsciousnessIntegrator

    gw = ConsciousnessIntegrator()
    d = gw.to_dict()
    assert "global_workspace" in d
    assert d["global_workspace"]["capacity"] == 3


def test_executive_metacognition_calibration():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE
    from brain.deliberation import DeliberationResult

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_executive_cognition=True,
        enable_metacognition_calibration=True,
        enable_dual_task_metrics=True,
    )
    brain.consciousness.metacognition = {"clarity": 0.8, "doubt": 0.1}
    brain.deliberation.last = DeliberationResult(
        choice="estudiar",
        choice_key="study",
        confidence=0.7,
        agency=0.6,
    )
    for _ in range(6):
        brain.working_memory.push(label=f"item{_}", modality="test")
    ex = ExecutiveCognitionStack()
    ex.post_deliberation(brain)
    assert brain.deliberation.last.confidence <= 0.7
