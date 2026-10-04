"""Tests connectome demo, sleep phases, typed memory."""

from dataclasses import replace

import numpy as np

from brain.experiment_flags import AblationFlags
from brain.memory_systems import TypedMemorySystems
from brain.mind import InfantApeBrain
from brain.profile import VIRTUAL_LARGE_PROFILE
from brain.regional_latency import latency_ms, RegionalSignalBus
from brain.sleep_architecture import SleepArchitecture, CYCLE_PHASES


def test_demo_profile_enables_scaffold():
    brain = InfantApeBrain(profile=VIRTUAL_LARGE_PROFILE, headless=True)
    from brain.experiment_flags import get_flags

    assert get_flags(brain).enable_connectome_scaffold is True


def test_regional_latency():
    assert latency_ms("hippocampus", "prefrontal") >= latency_ms("thalamus", "sensory_cortex")
    bus = RegionalSignalBus()
    bus.emit("thalamus", "prefrontal", 0.5, label="test")
    assert len(bus.pending) == 1


def test_typed_memory_classification():
    tm = TypedMemorySystems()
    assert tm.classify_episode(label="x", tags=["curriculum"], modality="text", motor=[]) == "semantic"
    assert tm.classify_episode(label="x", tags=["world", "explore", "intention"], modality="world", motor=[1]) == "procedural"


def test_sleep_architecture_phases():
    assert "nrem_deep" in CYCLE_PHASES
    assert "rem" in CYCLE_PHASES


def test_sleep_run_headless():
    brain = InfantApeBrain(headless=True)
    brain.brainstem.sleep_pressure = 0.85
    arch = SleepArchitecture()
    out = arch.run(brain, cycles=1, steps_per_cycle=48)
    assert out["sleep_mode"] == "nrem_rem_default"
    assert out["replay_mode"] == "default"
    assert "phase_log" in out


def test_procedural_bias_after_skill():
    brain = InfantApeBrain(headless=True)
    tm = brain.typed_memory
    for _ in range(3):
        tm.after_episode(
            brain,
            label="caminar@salón",
            tags=["world", "explore", "intention"],
            modality="world",
            motor=[2, 4],
            room="salón",
            valence=0.1,
            remembered=True,
        )
    bias = tm.procedural_motor_bias(brain, brain.deliberation.last.choice_key or "explore", "salón")
    assert float(bias.sum()) > 0
