"""Run seeded multi-Being TextWorld experiments offline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from services.being.models import Being
from services.worlds.textworld.world import TextWorld, DEFAULT_PLACES


@dataclass(frozen=True, slots=True)
class TextWorldExperiment:
    experiment_id: str
    seed: int
    ticks: int
    being_ids: tuple[str, ...]


def run_textworld_experiment(
    beings: Sequence[Being],
    *,
    seed: int,
    ticks: int,
    places: Sequence[str] | None = None,
    initial_places: Mapping[str, str] | None = None,
    experiment_id: str = "textworld-exp",
) -> dict[str, Any]:
    """Place Beings and run ticks. Identical seeds + beings order → identical traces."""
    if ticks < 1 or ticks > 5_000:
        raise ValueError("ticks must be in [1, 5000]")
    if len(beings) < 1:
        raise ValueError("need at least one Being")

    # Stable order by being_id for reproducibility across list shuffles.
    ordered = sorted(beings, key=lambda b: b.identity.being_id)
    world = TextWorld(seed=seed, places=tuple(places or DEFAULT_PLACES))
    world.reset(seed)

    for being in ordered:
        place = None if initial_places is None else initial_places.get(being.identity.being_id)
        world.place_being(being.identity.being_id, place)
        world.set_personality(being.identity.being_id, being.identity.core_personality.traits)

    tick_events: list[list[dict[str, Any]]] = []
    for _ in range(ticks):
        tick_events.append(world.tick())

    interactions = [e for e in world.events if e.get("event_type") == "BEING_INTERACTION"]
    return {
        "ok": True,
        "experiment": {
            "experiment_id": experiment_id,
            "software_component": "textworld-v1",
            "seed": seed,
            "ticks": ticks,
            "participants": [b.identity.being_id for b in ordered],
            "places": list(world.places),
        },
        "snapshot": world.snapshot(),
        "event_count": len(world.events),
        "interaction_count": len(interactions),
        "events": world.events,
        "tick_event_counts": [len(x) for x in tick_events],
        "trace_fingerprint": _fingerprint(world.events),
    }


def _fingerprint(events: Iterable[dict[str, Any]]) -> str:
    import hashlib
    import json

    # Stable content hash excluding random UUIDs/timestamps where possible.
    compact = []
    for ev in events:
        payload = dict(ev.get("payload") or {})
        # Drop volatile ids/timestamps inside nested interaction payloads.
        payload.pop("timestamp", None)
        payload.pop("interaction_id", None)
        compact.append(
            {
                "event_type": ev.get("event_type"),
                "tick": ev.get("tick"),
                "payload": payload,
            }
        )
    blob = json.dumps(compact, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
