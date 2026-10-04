"""Event protocol codec — fail closed on unknown event types."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

from protocols.being_interaction.codec import BeingInteraction, decode_interaction, encode_interaction
from protocols.being_interaction.privacy import sanitize_interaction_context

EVENT_PROTOCOL_VERSION = "nexo-event-v1"


class EventType(str, Enum):
    NODE_CONNECTED = "NODE_CONNECTED"
    BEING_CREATED = "BEING_CREATED"
    BEING_PLACED = "BEING_PLACED"
    BEING_INTERACTION = "BEING_INTERACTION"
    BEING_LEARNED = "BEING_LEARNED"
    BEING_FAILED = "BEING_FAILED"
    BEING_DISCOVERED = "BEING_DISCOVERED"
    EXPERIMENT_STARTED = "EXPERIMENT_STARTED"
    EXPERIMENT_COMPLETED = "EXPERIMENT_COMPLETED"
    MEMORY_CREATED = "MEMORY_CREATED"
    MEMORY_RECALLED = "MEMORY_RECALLED"
    KNOWLEDGE_CANDIDATE = "KNOWLEDGE_CANDIDATE"
    WORLD_TICK = "WORLD_TICK"


ALLOWED_EVENT_TYPES: frozenset[str] = frozenset(e.value for e in EventType)


class EventProtocolError(ValueError):
    """Invalid NEXO event."""


def validate_event_type(event_type: str) -> EventType:
    name = str(event_type or "").strip().upper()
    if name not in ALLOWED_EVENT_TYPES:
        raise EventProtocolError(f"event type not allowlisted: {event_type!r}")
    return EventType(name)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class NexoEvent:
    event_type: EventType
    tick: int
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: str = field(default_factory=_utc_now)
    version: str = EVENT_PROTOCOL_VERSION
    signature_hex: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "tick": int(self.tick),
            "timestamp": self.timestamp,
            "payload": dict(self.payload),
            "signature_hex": self.signature_hex,
        }


def encode_event(
    *,
    event_type: str | EventType,
    tick: int,
    payload: Mapping[str, Any] | None = None,
    event_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    et = event_type if isinstance(event_type, EventType) else validate_event_type(str(event_type))
    raw_payload = dict(payload or {})
    if et is EventType.BEING_INTERACTION:
        # Normalize nested BIP if present as flat fields or nested interaction.
        if "kind" in raw_payload or "action" in raw_payload:
            bip = encode_interaction(
                kind=str(raw_payload.get("kind") or raw_payload.get("action")),
                being_a=str(raw_payload.get("being_a") or ""),
                being_b=raw_payload.get("being_b"),
                tick=int(raw_payload.get("tick") or tick),
                place=raw_payload.get("place"),
                response=raw_payload.get("response"),
                outcome=str(raw_payload.get("outcome") or "ok"),
                context=dict(raw_payload.get("context") or {}),
                interaction_id=raw_payload.get("interaction_id"),
                timestamp=raw_payload.get("timestamp"),
            )
            payload_out = bip
        elif "interaction" in raw_payload:
            payload_out = decode_interaction(dict(raw_payload["interaction"])).to_dict()
        else:
            raise EventProtocolError("BEING_INTERACTION requires BIP fields")
    else:
        payload_out = sanitize_interaction_context(raw_payload)

    event = NexoEvent(
        event_type=et,
        tick=int(tick),
        payload=payload_out,
        event_id=event_id or uuid.uuid4().hex[:16],
        timestamp=timestamp or _utc_now(),
    )
    return event.to_dict()


def decode_event(data: Mapping[str, Any]) -> NexoEvent:
    if not isinstance(data, Mapping):
        raise EventProtocolError("event must be a mapping")
    version = str(data.get("version") or EVENT_PROTOCOL_VERSION)
    if version != EVENT_PROTOCOL_VERSION:
        raise EventProtocolError(f"unsupported event version: {version}")
    et = validate_event_type(str(data.get("event_type") or ""))
    payload = dict(data.get("payload") or {})
    if et is EventType.BEING_INTERACTION:
        bip = decode_interaction(payload)
        payload = bip.to_dict()
    else:
        payload = sanitize_interaction_context(payload)
    return NexoEvent(
        event_type=et,
        tick=int(data.get("tick") or 0),
        payload=payload,
        event_id=str(data.get("event_id") or uuid.uuid4().hex[:16]),
        timestamp=str(data.get("timestamp") or _utc_now()),
        version=EVENT_PROTOCOL_VERSION,
        signature_hex=None if data.get("signature_hex") is None else str(data.get("signature_hex")),
    )


def interaction_to_event(interaction: BeingInteraction | Mapping[str, Any], *, tick: int | None = None) -> dict[str, Any]:
    if isinstance(interaction, BeingInteraction):
        payload = interaction.to_dict()
        tick_v = interaction.tick if tick is None else tick
    else:
        payload = decode_interaction(interaction).to_dict()
        tick_v = int(payload.get("tick") if tick is None else tick)
    return encode_event(event_type=EventType.BEING_INTERACTION, tick=tick_v, payload=payload)
