"""Tests S2: ritmo circadiano corporal; no decide choice_key."""

from __future__ import annotations

from dataclasses import replace

from brain.environment import circadian_profile
from brain.experiment_flags import AblationFlags
from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE


def test_circadian_profile_night_has_more_sleep_drive():
    night = circadian_profile({"hour": 2, "minute": 0, "phase": "night"})
    afternoon = circadian_profile({"hour": 14, "minute": 0, "phase": "day"})

    assert night["sleep_drive"] > afternoon["sleep_drive"]
    assert afternoon["alertness"] > night["alertness"]
    assert 0.42 <= night["body_temp_target"] <= 0.62


def _brain_at(hour: int) -> InfantApeBrain:
    flags = replace(AblationFlags(), enable_circadian=True, disable_hippocampus=True)
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        headless=True,
        auto_save=False,
        experiment_flags=flags,
    )
    brain.world.clock.set_sim_time(hour, 0)
    brain.world.clock.minutes_per_tick = 1.0
    brain.body.fatigue = 0.2
    brain.brainstem.sleep_pressure = 0.2
    return brain


def test_circadian_tick_biases_sleep_pressure_and_fatigue():
    night = _brain_at(2)
    day = _brain_at(14)
    night_choice = night.deliberation.last.choice_key
    day_choice = day.deliberation.last.choice_key

    for _ in range(4):
        night.world_tick(steps=1)
        day.world_tick(steps=1)

    assert night.time_state()["circadian"]["sleep_drive"] > day.time_state()["circadian"]["sleep_drive"]
    assert night.brainstem.sleep_pressure > day.brainstem.sleep_pressure
    assert night.body.fatigue > day.body.fatigue
    # Circadiano modula estado corporal; no escribe choice_key directamente.
    assert night_choice == "wander"
    assert day_choice == "wander"


def test_time_state_hud_exposes_circadian_when_enabled():
    brain = _brain_at(8)
    brain.world_tick(steps=1)
    state = brain.time_state()

    assert "circadian" in state
    assert {"alertness", "sleep_drive", "cortisol_target", "body_temp_target"} <= set(
        state["circadian"].keys()
    )
