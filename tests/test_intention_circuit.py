"""Circuito intención → episodio → motor por spikes."""

from __future__ import annotations

import numpy as np

from brain.deliberation import PrefrontalDeliberation
from brain.intention import (
    deliberation_gate_context,
    merge_intention_into_sensory,
    record_spike_alignment,
)
from brain.mind import InfantApeBrain
from brain.subcortex import BasalGanglia


def test_merge_intention_changes_sensory():
    brain = InfantApeBrain()
    delib = PrefrontalDeliberation()
    drives = {"seek_food": 0.8, "seek_rest": 0.1}
    delib.run(
        brain,
        drives=drives,
        ambient={"hour": 8},
        attended=[],
        habit=None,
        surprise=0.1,
    )
    base = np.zeros(brain.n_sensory, dtype=np.float32)
    merged, meta = merge_intention_into_sensory(base, brain, delib)
    assert meta.choice_key == delib.last.choice_key
    assert meta.sensory_gain > 0.1
    assert not np.allclose(merged, base)


def test_basal_ganglia_spike_gated_deliberation():
    bg = BasalGanglia(n_motor=8)
    motor_v = np.array([0.1, 0.2, 0.1, 0.15, 0.9, 0.1, 0.1, 0.1], dtype=np.float32)
    spikes = np.zeros(8, dtype=bool)
    spikes[4] = True
    ctx = {
        "choice_key": "eat",
        "confidence": 0.7,
        "inhibited": False,
        "limbic_winner_key": "wander",
        "conflict": 0.0,
    }
    motor = bg.gate(
        motor_v,
        spikes,
        dopamine=0.5,
        drive=0.4,
        exploration=0.2,
        deliberation=ctx,
        pfc_inhibition=0.5,
    )
    assert 4 in motor


def test_world_tick_binds_intention():
    brain = InfantApeBrain()
    out = brain.world_tick(steps=1)
    assert out.get("alive", True) is not False or "lifecycle" in out
    if out.get("alive", True):
        ic = out.get("intention_circuit")
        assert ic is not None
        assert ic.get("choice_key")
        assert "deliberation" in out


def test_record_spike_alignment():
    from brain.intention import IntentionCircuit

    c = IntentionCircuit(choice_key="eat")
    spikes = np.zeros(8, dtype=bool)
    spikes[4] = True
    record_spike_alignment(c, motor_spikes=spikes, motor=[4, 1])
    assert c.spike_aligned
