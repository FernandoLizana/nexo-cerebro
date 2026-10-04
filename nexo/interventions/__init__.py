"""Intervenciones experimentales sobre el conectoma."""

from nexo.interventions.lesion import LesionSpec, LesionState
from nexo.interventions.profiles import LESION_NONE, LESION_REGISTRY, apply_lesion_profile, list_lesions

__all__ = [
    "LesionSpec",
    "LesionState",
    "LESION_NONE",
    "LESION_REGISTRY",
    "apply_lesion_profile",
    "list_lesions",
]
