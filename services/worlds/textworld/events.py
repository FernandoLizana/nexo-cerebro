"""TextWorld event helpers — thin adapters over formal BIP / Event protocols."""

from __future__ import annotations

from typing import Any

from protocols.being_interaction.codec import ALLOWED_INTERACTION_KINDS, encode_interaction
from protocols.events.codec import encode_event

# Back-compat alias used by older TextWorld imports/tests.
INTERACTION_TYPES = ALLOWED_INTERACTION_KINDS


def make_world_event(*, event_type: str, tick: int, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return encode_event(event_type=event_type, tick=tick, payload=payload or {})


def make_interaction_event(
    *,
    interaction_id: str,
    tick: int,
    being_a: str,
    being_b: str | None,
    action: str,
    response: str | None,
    outcome: str,
    place: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bip = encode_interaction(
        kind=action,
        being_a=being_a,
        being_b=being_b,
        tick=tick,
        place=place,
        response=response,
        outcome=outcome,
        context=context or {},
        interaction_id=interaction_id,
    )
    return encode_event(event_type="BEING_INTERACTION", tick=tick, payload=bip)
