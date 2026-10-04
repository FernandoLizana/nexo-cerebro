"""Tests S7: perfil 50k, motor continuo, multimodal."""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

from brain.experiment_flags import AblationFlags
from brain.motor_policy import ContinuousMotorPolicy
from brain.mind import InfantApeBrain
from brain.profile import (
    SCALE_10K_PROFILE,
    SCALE_50K_PROFILE,
    profile_neuron_count,
    resolve_experiment_profile,
)
from brain.profile import COMPACT_PROFILE
from brain.sensory_hub import SensoryPathwayHub


def test_scale_50k_active_lif_count():
    n = profile_neuron_count(SCALE_50K_PROFILE)
    assert n >= 50_000
    assert profile_neuron_count(SCALE_10K_PROFILE) >= 10_000
    assert SCALE_50K_PROFILE.name == "neuro-50k"
    # Separar LIF activo vs virtual en disco
    assert "LIF" in SCALE_50K_PROFILE.age_label or "activas" in SCALE_50K_PROFILE.age_label


def test_resolve_50k_profile():
    assert resolve_experiment_profile("50k") is SCALE_50K_PROFILE


def test_paper_s7_flags_off():
    f = AblationFlags()
    assert f.enable_lobe_virtual_inject is False
    assert f.enable_continuous_motor is False
    assert f.enable_multimodal_delays is False


def test_continuous_motor_does_not_set_choice():
    sd = Path(tempfile.mkdtemp(prefix="nexo_s7m_"))
    flags = replace(AblationFlags(), enable_continuous_motor=True, disable_hippocampus=True)
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
        experiment_flags=flags,
    )
    before = brain.deliberation.last.choice_key
    pol = ContinuousMotorPolicy()
    cmd = pol.decode(
        brain,
        [1, 3, 4],
        choice_key="eat",
        choice_target="fridge",
        confidence=0.7,
    )
    assert cmd.goal is not None
    discrete = pol.apply_to_world(brain, cmd)
    assert 4 in discrete or any(d in (0, 1, 2, 3) for d in discrete)
    # No mutó choice_key
    assert brain.deliberation.last.choice_key == before


def test_multimodal_ablation_vision():
    hub = SensoryPathwayHub()
    hub.use_delays = True
    hub.set_ablation("vision")
    assert hub.vision.enabled is False
    assert hub.audition.enabled is True
    n = 32
    import numpy as np

    vis = np.ones(n, dtype=np.float32)
    aud = np.zeros(n, dtype=np.float32)
    aud[:8] = 1.0
    # Con delays, primeros pushes pueden no salir aún
    for _ in range(4):
        fused, meta = hub.fuse_patterns(vision_pat=vis, audio_pat=aud, proprio_pat=None, n=n)
    assert "vision" not in (meta.get("present") or [])
    hub.clear_ablation()
    assert hub.vision.enabled is True


def test_lobe_virtual_inject_flag_wiring():
    sd = Path(tempfile.mkdtemp(prefix="nexo_s7l_"))
    flags = replace(
        AblationFlags(),
        enable_lobe_virtual_inject=True,
        disable_hippocampus=True,
    )
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
        experiment_flags=flags,
    )
    sensory = brain._world_sensory_vector()
    _, meta = brain._inject_virtual(sensory)
    assert "lobe_inject" in meta or meta.get("multimodal")
