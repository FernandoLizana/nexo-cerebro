"""Circuito hedónico — placer, saciedad, cansancio."""

from brain.hedonics import HedonicState
from brain.mind import InfantApeBrain


def test_hedonic_reward_eat_cooked():
    h = HedonicState()
    h.reward("eat_cooked", 0.5, label="sopa")
    assert h.satiety > 0.2
    assert h.pleasure >= 0.0
    assert h.last_reward == "sopa"


def test_hedonics_tick_syncs_body():
    brain = InfantApeBrain(headless=True)
    brain.body.hunger = 0.7
    brain.hedonics.tick(brain)
    assert brain.body.pleasure == brain.hedonics.pleasure
    assert brain.body.satiety == brain.hedonics.satiety
    assert brain.hedonics.craving > 0.2


def test_merged_drives_include_cook():
    brain = InfantApeBrain(headless=True)
    brain.hedonics.craving = 0.6
    drives = brain._merged_drives()
    assert drives.get("seek_cook", 0) > 0.1
    assert drives.get("seek_food", 0) > 0.2
