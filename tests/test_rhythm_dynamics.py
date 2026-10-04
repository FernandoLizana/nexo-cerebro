"""Bloque B — ritmos, oscilaciones y dinámica temporal (items 13–20)."""

from __future__ import annotations

import os

import numpy as np
import pytest

from dataclasses import replace

from brain.experiment_flags import AblationFlags
from brain.neuroanatomy import CorpusCallosum
from brain.oscillations import BrainOscillators
from brain.regional_latency import LOBE_LATENCY_MS, latency_ms
from brain.scn_clock import SCNClock


def test_pac_coupling_modulates_gamma():
    osc = BrainOscillators()
    low, pac_low = osc.pac_modulate(0.0, 1.0)
    high, pac_high = osc.pac_modulate(np.pi * 0.25, 1.0)
    assert pac_low != pac_high
    assert low != high


def test_sleep_spindle_burst():
    osc = BrainOscillators()
    osc.set_sleep_depth(0.85)
    osc.trigger_spindle_burst(ticks=5)
    snap = osc.step_full(sleep_state="nrem_deep")
    assert snap.spindle_active > 0.0
    assert snap.delta_amp > 0.35


def test_motor_beta_when_pending():
    osc = BrainOscillators()
    awake = osc.step_full(sleep_state="awake", motor_pending=False)
    motor = osc.step_full(sleep_state="awake", motor_pending=True)
    assert motor.motor_beta >= awake.motor_beta


def test_scn_jet_lag_recovery():
    scn = SCNClock()
    scn.apply_jet_lag_shift(3.0)
    assert abs(scn.phase_offset_min) > 100
    ambient = {"hour": 12, "minute": 0, "light_level": 0.9, "phase": "day"}
    for _ in range(40):
        scn.step(ambient, dt_min=10.0)
    assert abs(scn.phase_offset_min) < abs(180)


def test_scn_shifts_circadian_hour():
    scn = SCNClock()
    scn.phase_offset_min = 120.0
    ambient = {"hour": 10, "minute": 0, "light_level": 0.5, "phase": "day"}
    shifted = scn.shift_ambient(ambient)
    assert shifted["scn_hour"] == 12


def test_lobe_white_matter_latencies():
    assert latency_ms("occipital", "temporal") == LOBE_LATENCY_MS[("occipital", "temporal")]
    assert latency_ms("frontal", "motor") < latency_ms("occipital", "frontal")


def test_corpus_gamma_sync_with_pac():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_rhythm_pac=True,
    )
    brain.oscillators.step_full(sleep_state="awake")
    corpus = CorpusCallosum()
    out = corpus.integrate(brain)
    assert "gamma_sync" in out
    assert out["transfer"] > 0.0


def test_temporal_prediction_bias():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    os.environ["CEREBRO_TEMPORAL_PRED"] = "1"
    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_temporal_prediction=True,
        enable_circadian=True,
    )
    brain.world.clock.set_sim_time(7, 50)
    brain._last_env = {"circadian": {"alertness": 0.6, "sleep_drive": 0.2}}
    pred = brain.temporal_predictor.update(brain)
    assert pred["seek_food_eta_min"] <= 15
    drives = {"seek_food": 0.1}
    brain.temporal_predictor.apply_drive_bias(drives)
    assert drives["seek_food"] >= 0.1
