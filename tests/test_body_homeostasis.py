"""Tests Sprint 2 — cuerpo virtual y homeostasis."""

from __future__ import annotations

import pytest

from nexo.body.body_state import VirtualBody
from nexo.body.interoception import InteroceptiveChannel
from nexo.body.metabolism import MetabolismEngine
from nexo.homeostasis.drives import DriveField
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig
from nexo.random_streams import RandomStreams


def test_virtual_body_clamps():
    b = VirtualBody(energy=1.5, pain=-0.1)
    b.clamp()
    assert b.energy == 1.0
    assert b.pain == 0.0


def test_metabolism_basal_drain_bounded():
    body = VirtualBody(energy=0.8)
    engine = MetabolismEngine(basal_energy_drain=0.0006)
    for _ in range(100):
        engine.tick_basal(body)
    assert body.energy > 0.5


def test_drives_emerge_from_deviation_not_rules():
    body = VirtualBody(energy=0.25, social_need=0.7)
    drives = DriveField.from_body(body)
    assert drives.drives["hunger"] > drives.drives["curiosity"]
    assert drives.action_bias("eat") > drives.action_bias("explore")


def test_interoception_has_noise():
    ch = InteroceptiveChannel(noise_std=0.05)
    rng = RandomStreams.from_root_seed(1).sensory
    s1 = ch.perceive(variable="energy", true_value=0.6, rng=rng)
    s2 = ch.perceive(variable="energy", true_value=0.6, rng=rng)
    assert s1.perceived_value != s2.perceived_value or s1.uncertainty > 0


def test_integrated_v2_energy_not_collapsed_at_80_ticks():
    rt = IntegratedRuntime(IntegratedRuntimeConfig(seed=42, ticks=80, profile="integrated_v2"))
    result = rt.run()
    assert result["final_energy"] > 0.0
    assert result["final_energy"] < 1.0


def test_low_energy_increases_eat_bias_in_drives():
    body = VirtualBody(energy=0.2)
    drives_low = DriveField.from_body(body)
    body.energy = 0.8
    drives_high = DriveField.from_body(body)
    assert drives_low.action_bias("eat") > drives_high.action_bias("eat")


def test_same_seed_still_reproducible_with_body():
    r1 = IntegratedRuntime(IntegratedRuntimeConfig(seed=7, ticks=40))
    r2 = IntegratedRuntime(IntegratedRuntimeConfig(seed=7, ticks=40))
    assert r1.run()["trajectory_hash"] == r2.run()["trajectory_hash"]
