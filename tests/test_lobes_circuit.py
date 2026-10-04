"""Lóbulos, olfato, reflejos, veto PFC, estrés hipocampal."""

from __future__ import annotations

import numpy as np

from brain.hippocampus_core import HippocampalFormation
from brain.intention import enforce_pfc_motor_veto, hippocampus_stress_factor
from brain.lobes import LobeRouter, ROOM_ODORS
from brain.mind import InfantApeBrain
from brain.reflexes import BrainstemReflexes


def test_lobe_router_bands():
    brain = InfantApeBrain()
    intero = brain.body.encode(brain.n_sensory)
    raw = brain.world.encode_perception(brain.n_sensory, interoception=intero)
    sensory, olf, meta = brain.lobes.route(
        brain,
        world_raw=raw,
        vision={"percepts": []},
        temporal=np.zeros(8, dtype=np.float32),
        intero=intero,
        ambient={"hour": 12},
    )
    assert sensory.size == brain.n_sensory
    assert olf.size == brain.cortex.n_limbic
    assert meta["activity"]["frontal"] >= 0


def test_olfaction_bypasses_thalamus():
    brain = InfantApeBrain()
    brain.cortex.inject_olfactory(np.ones(brain.cortex.n_limbic, dtype=np.float32) * 0.5)
    assert brain.cortex._limbic_olfactory.any()


def test_hippocampus_stress_dampens():
    hf = HippocampalFormation(n_in=64, n_dg=32, n_ca3=32, n_ca1=24)
    sensory = np.random.default_rng(1).random(64).astype(np.float32) * 0.5
    out_low = hf.step(sensory, gain=0.1, theta_amp=1.0, mode="encode", stress=0.2)
    hf.reset()
    out_high = hf.step(sensory, gain=0.1, theta_amp=1.0, mode="encode", stress=0.85)
    assert out_high.mean() <= out_low.mean() + 0.05


def test_pfc_veto_blocks_limbic_motor():
    ctx = {
        "inhibited": True,
        "choice_key": "rest",
        "limbic_winner_key": "eat",
    }
    motor, veto = enforce_pfc_motor_veto([1], ctx, n_motor=8)
    assert veto
    assert motor == []


def test_reflexes_surprise():
    brain = InfantApeBrain()
    before = brain.amygdala.arousal
    brain.reflexes.step(brain, surprise=0.7, vision={})
    assert brain.amygdala.arousal >= before


def test_stress_factor():
    assert hippocampus_stress_factor(0.2) > hippocampus_stress_factor(0.8)


def test_room_odors_cover_kitchen():
    assert "cocina" in ROOM_ODORS
