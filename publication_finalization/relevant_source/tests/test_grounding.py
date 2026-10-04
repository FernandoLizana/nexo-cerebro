"""Tests S5: grounding sesga drives/sensory; no elige choice_key."""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

import numpy as np

from brain.experiment_flags import AblationFlags
from brain.grounding import apply_utterance_grounding, parse_grounding
from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE


def test_parse_grounding_fridge():
    hits = parse_grounding("Mira la nevera, hay comida")
    assert hits
    assert any(h.kind == "fridge" for h in hits)
    assert any(h.drive == "seek_food" for h in hits)


def test_paper_grounding_flag_off():
    assert AblationFlags().enable_grounding is False


def test_grounding_boosts_drive_not_choice():
    sd = Path(tempfile.mkdtemp(prefix="nexo_e5_"))
    flags = replace(AblationFlags(), enable_grounding=True, disable_hippocampus=True)
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
        experiment_flags=flags,
    )
    choice_before = brain.deliberation.last.choice_key
    before = float(brain._merged_drives().get("seek_food", 0.0))
    apply_utterance_grounding(brain, "Ve a la nevera por comida", duration_ticks=5)
    after = float(brain._merged_drives().get("seek_food", 0.0))
    assert after > before
    # Grounding no escribe choice_key
    assert brain.deliberation.last.choice_key == choice_before
    out = brain.caregiver_speak("hay comida en la nevera")
    assert "grounding" in out
    assert out["grounding"].get("agency_note") or "hits" in out["grounding"]
    assert brain.grounding.hits


def test_grounding_off_no_boost_from_apply_path():
    sd = Path(tempfile.mkdtemp(prefix="nexo_e5off_"))
    flags = replace(AblationFlags(), enable_grounding=False, disable_hippocampus=True)
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
        experiment_flags=flags,
    )
    out = brain.caregiver_speak("mira la nevera")
    assert "grounding" not in out or out.get("grounding") is None


def test_grounding_can_guide_motivated_navigation_without_forcing_choice():
    sd = Path(tempfile.mkdtemp(prefix="nexo_e5move_"))
    flags = replace(AblationFlags(), enable_grounding=True, disable_hippocampus=True)
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
        experiment_flags=flags,
    )
    brain.world.ensure_home()
    brain.world.agent_x = 500.0
    brain.world.agent_y = 80.0
    brain.world.ensure_agent_free()
    brain.body.hunger = 0.65
    brain.body.fatigue = 0.1
    fridge = brain.world.furniture_center("fridge")
    assert fridge is not None
    before_distance = float(
        np.hypot(brain.world.agent_x - fridge[0], brain.world.agent_y - fridge[1])
    )
    choice_before_speech = brain.deliberation.last.choice_key

    brain.caregiver_speak("mira la nevera, hay comida")

    # La frase no decide la acción de forma directa.
    assert brain.deliberation.last.choice_key == choice_before_speech
    choices = []
    for _ in range(12):
        out = brain.world_tick(steps=1)
        choices.append((out.get("deliberation") or {}).get("choice_key"))

    after_distance = float(
        np.hypot(brain.world.agent_x - fridge[0], brain.world.agent_y - fridge[1])
    )
    assert any(choice in ("eat", "harvest") for choice in choices)
    assert after_distance < before_distance
