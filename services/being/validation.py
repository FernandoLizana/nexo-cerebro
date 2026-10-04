"""Validation for Being parts — experimental bounds only."""

from __future__ import annotations

from services.being.models import (
    BEING_FORMAT_VERSION,
    PERSONALITY_TRAITS,
    BeingIdentity,
    CognitiveConfiguration,
    MemoryBundle,
    TemporaryState,
)


class BeingValidationError(ValueError):
    """Invalid Being payload."""


def validate_being_parts(
    identity: BeingIdentity,
    memory: MemoryBundle,
    state: TemporaryState,
    cognitive: CognitiveConfiguration,
) -> None:
    if not identity.being_id.strip():
        raise BeingValidationError("being_id required")
    if not identity.name.strip():
        raise BeingValidationError("name required")
    if identity.format_version != BEING_FORMAT_VERSION:
        raise BeingValidationError(
            f"unsupported format_version {identity.format_version!r}; expected {BEING_FORMAT_VERSION}"
        )
    traits = identity.core_personality.traits
    missing = [t for t in PERSONALITY_TRAITS if t not in traits]
    if missing:
        raise BeingValidationError(f"missing personality traits: {missing}")
    for key, value in traits.items():
        if key not in PERSONALITY_TRAITS:
            raise BeingValidationError(f"unknown personality trait: {key}")
        if not 0.0 <= float(value) <= 1.0:
            raise BeingValidationError(f"trait {key} out of bounds: {value}")
    if not 0.05 <= float(cognitive.cognitive_budget) <= 1.0:
        raise BeingValidationError("cognitive_budget must be in [0.05, 1.0]")
    if cognitive.memory_level not in {"minimal", "standard", "rich"}:
        raise BeingValidationError("memory_level must be minimal|standard|rich")
    # memory/state already clamped on serialize; ensure no huge blobs in S3
    if len(memory.episodic) > 10_000 or len(memory.semantic) > 10_000:
        raise BeingValidationError("memory store exceeds S3 soft limit")
    _ = state  # validated via TemporaryState.to_dict clamps
