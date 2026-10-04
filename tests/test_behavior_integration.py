"""Tests for unified brain behavior integration."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from brain import InfantApeBrain
from brain.behavior_integration import (
    choice_allows_event,
    deliberation_track_boost,
    pick_desk_study_event,
    sleep_study_weights,
)
from brain.experiment_flags import AblationFlags
from brain.profile import COMPACT_PROFILE


@pytest.fixture
def brain(tmp_path):
    flags = replace(AblationFlags(), enable_sleep_study=True)
    b = InfantApeBrain(profile=COMPACT_PROFILE, state_dir=tmp_path, experiment_flags=flags)
    b.headless = True
    b.world.ensure_home()
    return b


def test_choice_allows_event():
    assert choice_allows_event("research", "web_search")
    assert not choice_allows_event("research", "eat")
    assert choice_allows_event("wander", "eat")


def test_pick_desk_research_is_web(brain):
    brain.world.agent_x = 200.0
    brain.world.agent_y = 210.0
    ev = pick_desk_study_event(brain, choice_key="research", curiosity=0.5)
    assert ev["type"] == "web_search"


def test_pick_desk_study_uses_track_progress(brain):
    brain.world.agent_x = 200.0
    brain.world.agent_y = 210.0
    ev = pick_desk_study_event(brain, choice_key="clinical", curiosity=0.4)
    assert ev["type"] == "clinical_study"


def test_deliberation_boost_for_clinical_track(brain):
    assert deliberation_track_boost(brain, "clinical") > 0.1


def test_sleep_weights_reflect_progress(brain):
    w = sleep_study_weights(brain)
    assert "clinical" in w
    assert sum(w.values()) > 0.5
