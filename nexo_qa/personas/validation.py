"""Persona validation — reject invalid trait configs."""

from __future__ import annotations

import math
from typing import Any

TRAIT_FIELDS = frozenset(
    {
        "working_memory_capacity",
        "attention_persistence",
        "distractibility",
        "visual_search_efficiency",
        "risk_aversion",
        "patience",
        "frustration_tolerance",
        "exploration_tendency",
        "digital_literacy",
        "semantic_confidence",
        "initial_fatigue",
        "impulsivity",
        "learning_rate_modifier",
        "metacognitive_sensitivity",
        "fatigue_rate_modifier",
    }
)

FLOAT_TRAITS = TRAIT_FIELDS - {"working_memory_capacity"}


def validate_traits(data: dict[str, Any], *, strict: bool = True) -> list[str]:
    errors: list[str] = []
    if strict:
        unknown = set(data.keys()) - TRAIT_FIELDS
        if unknown:
            errors.append(f"unknown fields: {sorted(unknown)}")
    cap = data.get("working_memory_capacity", 4)
    try:
        cap_i = int(cap)
        if cap_i < 1 or cap_i > 12:
            errors.append("working_memory_capacity out of range [1,12]")
    except (TypeError, ValueError):
        errors.append("working_memory_capacity must be integer")
    for key in FLOAT_TRAITS:
        if key not in data:
            continue
        val = data[key]
        try:
            f = float(val)
        except (TypeError, ValueError):
            errors.append(f"{key} must be numeric")
            continue
        if math.isnan(f) or math.isinf(f):
            errors.append(f"{key} cannot be NaN/Infinity")
        if key == "learning_rate_modifier":
            if f < 0.1 or f > 3.0:
                errors.append("learning_rate_modifier out of range [0.1,3.0]")
        elif key == "fatigue_rate_modifier":
            if f < 0.1 or f > 3.0:
                errors.append("fatigue_rate_modifier out of range [0.1,3.0]")
        elif f < 0.0 or f > 1.0:
            errors.append(f"{key} out of range [0,1]")
    return errors
