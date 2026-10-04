"""BIP codec — serialize/deserialize Being interactions (fail closed)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

from protocols.being_interaction.privacy import sanitize_interaction_context

BIP_VERSION = "bip-v1"


class InteractionKind(str, Enum):
    MESSAGE = "MESSAGE"
    OBSERVE = "OBSERVE"
    REQUEST = "REQUEST"
    OFFER = "OFFER"
    HELP = "HELP"
    REJECT = "REJECT"
    PLAY = "PLAY"
    TEACH = "TEACH"
    ASK = "ASK"
    SHARE_MEMORY = "SHARE_MEMORY"
    SHARE_DISCOVERY = "SHARE_DISCOVERY"
    # TextWorld locomotion / maintenance (still allowlisted BIP extensions)
    GREET = "GREET"
    MOVE = "MOVE"
    REST = "REST"
    FORAGE = "FORAGE"


ALLOWED_INTERACTION_KINDS: frozenset[str] = frozenset(k.value for k in InteractionKind)


class BIPError(ValueError):
    """Invalid BIP payload."""


def validate_interaction_kind(kind: str) -> InteractionKind:
    name = str(kind or "").strip().upper()
    if name not in ALLOWED_INTERACTION_KINDS:
        raise BIPError(f"interaction kind not allowlisted: {kind!r}")
    return InteractionKind(name)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class BeingInteraction:
    """Canonical BIP message (unsigned in S6; signing reserved for later)."""

    interaction_id: str
    kind: InteractionKind
    being_a: str
    being_b: str | None
    tick: int
    place: str | None
    response: str | None = None
    outcome: str = "ok"
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_utc_now)
    version: str = BIP_VERSION
    # Reserved for S7+ envelopes; never required in S6.
    signature_hex: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "interaction_id": self.interaction_id,
            "kind": self.kind.value,
            "being_a": self.being_a,
            "being_b": self.being_b,
            "tick": int(self.tick),
            "place": self.place,
            "response": self.response,
            "outcome": self.outcome,
            "context": dict(self.context),
            "timestamp": self.timestamp,
            "signature_hex": self.signature_hex,
        }


def encode_interaction(
    *,
    kind: str | InteractionKind,
    being_a: str,
    being_b: str | None,
    tick: int,
    place: str | None = None,
    response: str | None = None,
    outcome: str = "ok",
    context: Mapping[str, Any] | None = None,
    interaction_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Validate + sanitize + serialize a BIP interaction."""
    if not str(being_a).strip():
        raise BIPError("being_a required")
    kind_e = kind if isinstance(kind, InteractionKind) else validate_interaction_kind(str(kind))
    clean_context = sanitize_interaction_context(dict(context or {}))
    msg = BeingInteraction(
        interaction_id=interaction_id or f"ix-{uuid.uuid4().hex[:16]}",
        kind=kind_e,
        being_a=str(being_a),
        being_b=None if being_b is None else str(being_b),
        tick=int(tick),
        place=None if place is None else str(place),
        response=None if response is None else str(response),
        outcome=str(outcome or "ok"),
        context=clean_context,
        timestamp=timestamp or _utc_now(),
    )
    return msg.to_dict()


def decode_interaction(data: Mapping[str, Any]) -> BeingInteraction:
    """Deserialize BIP payload; reject unknown kinds and dirty context."""
    if not isinstance(data, Mapping):
        raise BIPError("interaction must be a mapping")
    version = str(data.get("version") or BIP_VERSION)
    if version != BIP_VERSION:
        raise BIPError(f"unsupported BIP version: {version}")
    kind = validate_interaction_kind(str(data.get("kind") or data.get("action") or ""))
    being_a = str(data.get("being_a") or "").strip()
    if not being_a:
        raise BIPError("being_a required")
    context = sanitize_interaction_context(dict(data.get("context") or {}))
    return BeingInteraction(
        interaction_id=str(data.get("interaction_id") or f"ix-{uuid.uuid4().hex[:16]}"),
        kind=kind,
        being_a=being_a,
        being_b=None if data.get("being_b") is None else str(data.get("being_b")),
        tick=int(data.get("tick") or 0),
        place=None if data.get("place") is None else str(data.get("place")),
        response=None if data.get("response") is None else str(data.get("response")),
        outcome=str(data.get("outcome") or "ok"),
        context=context,
        timestamp=str(data.get("timestamp") or _utc_now()),
        version=BIP_VERSION,
        signature_hex=None if data.get("signature_hex") is None else str(data.get("signature_hex")),
    )
