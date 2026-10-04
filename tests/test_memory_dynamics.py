"""Bloque E — dinámica de memoria (items 45–56)."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from brain.consolidation import forgetting_retention
from brain.episodic_context import build_context_vector, build_rich_extras, fuse_episodic_pattern
from brain.experiment_flags import AblationFlags
from brain.memory_dynamics import FlashbulbRegistry, MemoryDynamicsStack, MemoryInterferenceTracker


def test_forgetting_curve_emotional_slower():
    fresh = forgetting_retention(age_hours=24, emotional=0.0)
    emotional = forgetting_retention(age_hours=24, emotional=0.8)
    assert emotional > fresh


def test_rich_episodic_context_vector():
    ctx = build_context_vector(
        body={"hunger": 0.5, "thirst": 0.3},
        room="cocina",
        motor=[1, 2],
        olfaction={"intensity": 0.6, "valence_hint": 0.2},
        affect={"valence": 0.4, "arousal": 0.7},
        posture={"equilibrium": 0.8, "signal": 0.5},
    )
    assert ctx.size == 40
    assert float(ctx[32]) > 0.0


def test_fuse_episodic_with_rich():
    sensory = np.random.rand(64).astype(np.float32)
    fused, ctx = fuse_episodic_pattern(
        sensory,
        n=64,
        body={"hunger": 0.4},
        room="casa",
        olfaction={"intensity": 0.5},
    )
    assert fused.size == 64
    assert ctx.size >= 32


def test_flashbulb_mark():
    fb = FlashbulbRegistry()
    assert fb.mark(key="k1", label="dolor fuerte", valence=-0.7, arousal=0.8)
    assert fb.replay_boost("k1") > 0.3
    assert not fb.mark(key="k2", label="neutral", valence=0.1, arousal=0.2)


def test_interference_penalty():
    tr = MemoryInterferenceTracker()
    for i in range(6):
        tr.note_encode(f"evento {i % 2}")
    assert tr.recall_penalty() > 0.0


def test_memory_dynamics_on_encode():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_memory_dynamics=True,
        enable_flashbulb_memory=True,
        enable_autobiographical_timeline=True,
    )
    md = MemoryDynamicsStack()
    out = md.on_encode(
        brain,
        {"key": "test_key"},
        label="momento intenso con Nira",
        valence=0.65,
        arousal=0.75,
        tags=["social"],
    )
    assert out.get("flashbulb") is True
    assert len(md.autobiography.events) >= 1


def test_adjust_recall_score_flashbulb_boost():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_memory_dynamics=True,
        enable_forgetting_curve=True,
        enable_flashbulb_memory=True,
    )
    md = MemoryDynamicsStack()
    md.flashbulb.mark(key="fb1", label="symbol", valence=0.8, arousal=0.9)
    mem = {"key": "fb1", "valence": 0.8, "arousal": 0.9, "updated_at": 0}
    boosted = md.adjust_recall_score(brain, mem, 0.6)
    plain = md.adjust_recall_score(brain, {"key": "x", "updated_at": 0}, 0.6)
    assert boosted >= plain


def test_working_memory_limited_capacity():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(AblationFlags(), enable_limited_wm=True)
    brain.working_memory.limited = True
    for i in range(12):
        brain.working_memory.push(label=f"slot{i}", modality="test", salience=0.5)
    assert len(brain.working_memory.slots) <= brain.working_memory.effective_capacity()
