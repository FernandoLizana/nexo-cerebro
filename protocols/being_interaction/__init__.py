"""Being Interaction Protocol (BIP) — allowlisted interaction kinds only."""

from __future__ import annotations

from protocols.being_interaction.codec import (
    BIP_VERSION,
    BeingInteraction,
    InteractionKind,
    decode_interaction,
    encode_interaction,
    validate_interaction_kind,
)
from protocols.being_interaction.privacy import PrivacyViolation, sanitize_interaction_context

__all__ = [
    "BIP_VERSION",
    "BeingInteraction",
    "InteractionKind",
    "PrivacyViolation",
    "decode_interaction",
    "encode_interaction",
    "sanitize_interaction_context",
    "validate_interaction_kind",
]
