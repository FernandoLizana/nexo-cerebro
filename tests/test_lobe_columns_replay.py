"""Columnas lóbulo + replay diurno."""

from __future__ import annotations

import numpy as np

from brain.daytime_replay import DaytimeReplay
from brain.lobe_cortex import LobeCorticalColumns
from brain.mind import InfantApeBrain


def test_lobe_columns_bind_and_step():
    brain = InfantApeBrain()
    vecs = {
        "occipital": np.ones(24, dtype=np.float32) * 0.6,
        "temporal": np.zeros(24, dtype=np.float32),
        "parietal": np.zeros(24, dtype=np.float32),
        "frontal": np.zeros(24, dtype=np.float32),
    }
    act = brain.lobe_cortex.step(brain.cortex, vectors=vecs, gain=0.5)
    assert act["occipital"] > 0.05
    assert float(brain.cortex._lobe_boost_sensory.max()) > 0


def test_lobe_columns_increase_neuron_count():
    brain = InfantApeBrain()
    assert brain.lobe_cortex.n_neurons == 96
    assert brain.n_total > 1400


def test_daytime_replay_on_surprise():
    brain = InfantApeBrain()
    brain.hippocampus.consolidate(
        np.random.default_rng(2).random(brain.n_sensory).astype(np.float32),
        label="evento sorpresa",
        modality="world",
        motor=[1],
        valence=0.2,
        arousal=0.7,
    )
    dr = brain.daytime_replay.maybe_replay(brain, surprise=0.75, trigger_label="test")
    assert dr is not None
    assert dr.get("steps", 0) >= 12


def test_daytime_replay_cooldown():
    brain = InfantApeBrain()
    brain.hippocampus.consolidate(
        np.ones(brain.n_sensory, dtype=np.float32) * 0.3,
        label="a",
        modality="world",
        motor=[],
        valence=0.0,
        arousal=0.5,
    )
    brain.daytime_replay.maybe_replay(brain, surprise=0.8)
    assert brain.daytime_replay.maybe_replay(brain, surprise=0.9) is None
