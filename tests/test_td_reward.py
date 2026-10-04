"""Tests: dopamina TD no usurpa libre albedrío (agency / deliberación)."""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

import numpy as np

from brain.experiment_flags import AblationFlags, apply_condition
from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE
from brain.td_reward import TD_GO_BIAS_MAX, TDRewardSystem


def _brain(**kwargs) -> InfantApeBrain:
    sd = Path(tempfile.mkdtemp(prefix="nexo_td_"))
    return InfantApeBrain(
        profile=COMPACT_PROFILE,
        headless=True,
        auto_save=False,
        state_dir=sd,
        **kwargs,
    )


def test_td_observe_updates_value_and_delta():
    td = TDRewardSystem(alpha=0.5, gamma=0.9)
    d1 = td.observe(
        prev_room="cocina",
        prev_drive="seek_food",
        action="eat",
        reward=0.8,
        next_room="cocina",
        next_drive="seek_food",
        hour=12,
    )
    assert abs(d1) > 0.01
    assert td.updates == 1
    v = td.predicted_value("cocina", "seek_food", "eat", hour=12)
    assert v > 0


def test_go_biases_capped_and_attenuated_by_conflict():
    td = TDRewardSystem()
    td.values["jardín|seek_food|4::eat"] = 2.0
    low = td.go_biases(
        room="jardín",
        top_drive="seek_food",
        hour=12,
        action_keys=["eat", "wander"],
        conflict=0.0,
    )
    high = td.go_biases(
        room="jardín",
        top_drive="seek_food",
        hour=12,
        action_keys=["eat", "wander"],
        conflict=0.9,
    )
    assert abs(low.get("eat", 0)) <= TD_GO_BIAS_MAX + 1e-6
    assert abs(high.get("eat", 0)) < abs(low.get("eat", 0))


def test_td_does_not_force_winner_when_pfc_inhibits():
    """Con TD ON, force_limbic sigue siendo la única vía de forzar ganador."""
    flags = replace(
        AblationFlags(),
        enable_td_reward=True,
        force_limbic_winner=False,
        disable_hippocampus=True,  # evita mismatch dim compact vs store legado
    )
    brain = _brain(experiment_flags=flags)
    brain.td_reward.values["casa|seek_food|4::eat"] = 5.0
    brain.body.hunger = 0.9
    out = brain.world_tick(steps=1)
    delib = out.get("deliberation") or {}
    assert "agency" in delib
    assert "choice_key" in delib
    assert isinstance(delib.get("inhibited"), bool)


def test_paper_default_td_off():
    assert AblationFlags().enable_td_reward is False
    assert apply_condition("full").enable_td_reward is False


def test_td_on_headless_learns():
    flags = replace(AblationFlags(), enable_td_reward=True, disable_hippocampus=True)
    brain = _brain(experiment_flags=flags)
    np.random.seed(0)
    brain.world._rng = np.random.default_rng(0)
    before = brain.td_reward.updates
    brain.world_tick(steps=1)
    assert brain.td_reward.updates >= before + 1
    d = brain.td_reward.to_dict()
    assert d["agency_note"]
    assert "go_bias_max" in d
