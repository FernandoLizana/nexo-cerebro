"""Selección de perfil para experimentos batch."""

from __future__ import annotations

import os

from brain.profile import (
    COMPACT_PROFILE,
    NeuroProfile,
    SCALE_10K_PROFILE,
    SCALE_50K_PROFILE,
    profile_neuron_count,
    resolve_experiment_profile,
)

__all__ = [
    "COMPACT_PROFILE",
    "SCALE_10K_PROFILE",
    "SCALE_50K_PROFILE",
    "profile_neuron_count",
    "resolve_experiment_profile",
    "profile_label",
]


def profile_label(p: NeuroProfile) -> str:
    return f"{p.name} (~{profile_neuron_count(p)} neurons)"


def set_profile_env(name: str) -> NeuroProfile:
    os.environ["CEREBRO_EXPERIMENT_PROFILE"] = name
    return resolve_experiment_profile(name)
