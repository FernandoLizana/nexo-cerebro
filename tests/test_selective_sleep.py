"""Tests Sprint S4: sueño selectivo no usurpa agency; modos de replay."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np

from brain.experiment_flags import AblationFlags
from brain.memory_store import EpisodicMemoryStore
from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE


def test_paper_selective_sleep_flag_off():
    assert AblationFlags().enable_selective_sleep is False


def test_replay_modes_change_weights():
    sd = Path(tempfile.mkdtemp(prefix="nexo_e4w_"))
    store = EpisodicMemoryStore(sd, pattern_dim=64)
    cold = np.zeros(64, dtype=np.float32)
    cold[0] = 1.0
    hot = np.zeros(64, dtype=np.float32)
    hot[1] = 1.0
    store.store(
        "k_cold",
        cold,
        label="dato neutro",
        modality="text",
        motor=[],
        valence=0.05,
        arousal=0.2,
        tags=["neutral"],
    )
    store.store(
        "k_hot",
        hot,
        label="terror incendio",
        modality="text",
        motor=[],
        valence=-0.9,
        arousal=0.8,
        tags=["emotional"],
    )
    # Force many samples
    np.random.seed(0)
    picks_sel = []
    picks_uni = []
    for _ in range(40):
        a = store.sample_for_replay(replay_mode="selective")
        b = store.sample_for_replay(replay_mode="uniform")
        picks_sel.append(a["key"] if a else "")
        picks_uni.append(b["key"] if b else "")
    assert picks_sel.count("k_hot") > picks_sel.count("k_cold")
    # Uniform should be closer to balanced
    assert abs(picks_uni.count("k_hot") - picks_uni.count("k_cold")) < abs(
        picks_sel.count("k_hot") - picks_sel.count("k_cold")
    ) or picks_uni.count("k_hot") <= picks_sel.count("k_hot")


def test_active_forgetting_reduces_neutral_count():
    sd = Path(tempfile.mkdtemp(prefix="nexo_e4f_"))
    store = EpisodicMemoryStore(sd, pattern_dim=32)
    p = np.ones(32, dtype=np.float32)
    store.store(
        "n1",
        p,
        label="neutro",
        modality="text",
        motor=[],
        valence=0.05,
        arousal=0.2,
        tags=["neutral"],
    )
    store.record_sleep_replay("n1")
    store.record_sleep_replay("n1")
    row = store._db.execute("SELECT count FROM memories WHERE key='n1'").fetchone()
    assert int(row["count"]) >= 3
    n = store.active_forgetting_pass(max_abs_valence=0.22)
    assert n >= 1
    row2 = store._db.execute("SELECT count FROM memories WHERE key='n1'").fetchone()
    assert int(row2["count"]) == int(row["count"]) - 1


def test_sleep_selective_runs_and_reports_mode():
    sd = Path(tempfile.mkdtemp(prefix="nexo_e4s_"))
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
    )
    brain.experience(
        text="Un miedo intenso ante el fuego.",
        label="miedo fuego",
        tags=["miedo", "emotional"],
        repeats=1,
        steps_per_repeat=12,
    )
    brain.memory_store.set_memory_affect(query="miedo fuego", valence=-0.7, arousal=0.8)
    out = brain.sleep(cycles=1, steps_per_cycle=40, replay_mode="selective")
    assert out.get("replay_mode") == "selective"
    assert "agency_note" in (brain.sleep_arch.run.__doc__ or "") or out.get("slept")
    # Sleep must not clear deliberation agency path
    tick = brain.world_tick(steps=1)
    assert "deliberation" in tick
    assert "choice_key" in (tick.get("deliberation") or {})
