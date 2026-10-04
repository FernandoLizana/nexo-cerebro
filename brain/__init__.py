"""Modelo neurobiológico abreviado (corteza E/I, hipocampo, moduladores)."""

from .cortex import CorticalNetwork
from .mind import HumanBrain, InfantApeBrain
from .persist import BrainPersistence
from .profile import DEFAULT_PROFILE, INFANT_APE_PROFILE, NeuroProfile, VIRTUAL_LARGE_PROFILE, resolve_default_profile

__all__ = [
    "CorticalNetwork",
    "HumanBrain",
    "InfantApeBrain",
    "NeuroProfile",
    "DEFAULT_PROFILE",
    "INFANT_APE_PROFILE",
    "VIRTUAL_LARGE_PROFILE",
    "resolve_default_profile",
    "BrainPersistence",
]
