"""Re-export de condiciones de ablación (CLI y notebooks)."""

from brain.experiment_flags import (
    CONDITION_NAMES,
    AblationFlags,
    apply_condition,
    get_flags,
)

__all__ = ["AblationFlags", "CONDITION_NAMES", "apply_condition", "get_flags"]
