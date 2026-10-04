"""Tests Sprint 3 — percepción predictiva y tálamo."""

from __future__ import annotations

import numpy as np
import pytest

from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig
from nexo.perception.hierarchy import PredictiveHierarchy
from nexo.perception.prediction_error import compute_surprise, weighted_prediction_error
from nexo.perception.precision_weighting import PrecisionEstimator
from nexo.random_streams import RandomStreams
from nexo.thalamus.context_gate import ContextGate
from nexo.thalamus.relay import SensoryPacket, ThalamicRelay
from nexo.thalamus.reticular import ReticularNucleus


def test_weighted_prediction_error_scales_with_precision():
    obs = np.array([1.0, 0.0, 0.0])
    pred = np.array([0.0, 0.0, 0.0])
    e_low = weighted_prediction_error(obs, pred, 0.2)
    e_high = weighted_prediction_error(obs, pred, 0.9)
    assert np.linalg.norm(e_high) > np.linalg.norm(e_low)


def test_habituation_reduces_surprise_over_repeated_input():
    h = PredictiveHierarchy()
    obs = np.array([0.8, 0.2, 0.1])
    r1 = h.update(modality="food", observation=obs, precision=0.7)
    for _ in range(8):
        h.update(modality="food", observation=obs, precision=0.7)
    r9 = h.update(modality="food", observation=obs, precision=0.7)
    assert r9.surprise <= r1.surprise


def test_reticular_suppresses_habituated_modality():
    ret = ReticularNucleus(inhibition_strength=0.7)
    for _ in range(10):
        ret.update_habituation("distractor", 0.05)
    mask = ret.mask(["distractor", "danger"], goals=("survive",))
    assert mask["distractor"] < mask["danger"]


def test_thalamic_relay_competes_modalities():
    relay = ThalamicRelay(minimum_gate=0.2)
    packets = [
        SensoryPacket("food", (1.0, 0.2, 0.1), 0.8),
        SensoryPacket("distractor", (0.8, 0.9, 0.1), 0.3),
    ]
    gated = relay.relay(packets, context_gain=0.9, reticular_mask={"food": 1.0, "distractor": 0.4})
    gains = {g.modality: g.gain for g in gated}
    assert gains["food"] > gains["distractor"]


def test_precision_higher_when_attended():
    est = PrecisionEstimator()
    p0 = est.estimate(salience=0.5, modality="food", attention_focus=())
    p1 = est.estimate(salience=0.5, modality="food", attention_focus=("food",))
    assert p1 > p0


def test_predictive_mode_produces_prediction_errors():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=42, ticks=30, perception_mode="predictive", profile="test")
    )
    rt.run()
    errors = [e for e in rt.state_store.event_log if e.event_type == "perception.prediction_error"]
    assert len(errors) >= 5


def test_predictive_differs_from_legacy_trajectory():
    legacy = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=42, ticks=40, perception_mode="legacy")
    ).run()
    predictive = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=42, ticks=40, perception_mode="predictive")
    ).run()
    assert legacy["trajectory_hash"] != predictive["trajectory_hash"]


def test_same_seed_predictive_reproducible():
    r1 = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=99, ticks=35, perception_mode="predictive")
    ).run()
    r2 = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=99, ticks=35, perception_mode="predictive")
    ).run()
    assert r1["trajectory_hash"] == r2["trajectory_hash"]


def test_context_gate_lowers_under_sleep_pressure():
    gate = ContextGate()
    g_wake = gate.compute(active_goals=("survive",), stress=0.1, sleep_pressure=0.1)
    g_sleepy = gate.compute(active_goals=("survive",), stress=0.1, sleep_pressure=0.8)
    assert g_wake > g_sleepy


def test_integrated_v3_runs():
    from pathlib import Path

    from nexo.integrated_runtime import runtime_from_config, _repo_root

    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v3.yaml")
    result = rt.run(40)
    assert result["perception_mode"] == "predictive"
    assert result["mean_surprise"] >= 0.0
