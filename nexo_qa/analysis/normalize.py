"""Event normalization — NEXO events + world trace → CognitiveQAEvent."""

from __future__ import annotations

from typing import Any

from nexo_qa.analysis.models import CognitiveQAEvent, RawRunTrace, _new_id

FORBIDDEN_EVIDENCE_KEYS = frozenset(
    {"selector", "xpath", "css", "locator", "data-testid", "password", "token", "secret"}
)


def _scrub_payload(payload: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, val in payload.items():
        lk = key.lower()
        if lk in FORBIDDEN_EVIDENCE_KEYS or "password" in lk or "token" in lk:
            continue
        if isinstance(val, dict):
            clean[key] = _scrub_payload(val)
        elif isinstance(val, list):
            clean[key] = [_scrub_payload(v) if isinstance(v, dict) else v for v in val]
        else:
            clean[key] = val
    return clean


def normalize_events(raw: RawRunTrace) -> list[CognitiveQAEvent]:
    """Adapt raw trace into normalized CognitiveQAEvent list."""
    run_id = raw.run_id
    goal_id = raw.metadata.get("goal_id")
    persona_id = raw.metadata.get("persona_id")
    normalized: list[CognitiveQAEvent] = []

    for ev in raw.events:
        payload = _scrub_payload(dict(ev.get("payload") or {}))
        action_id = payload.get("action") or payload.get("selected_action_id") or payload.get("choice_key")
        normalized.append(
            CognitiveQAEvent(
                event_id=_new_id("qaev"),
                trace_id=str(ev.get("trace_id") or _new_id("tr")),
                run_id=run_id,
                tick=int(ev.get("tick", 0)),
                simulation_time=float(ev.get("simulation_time", 0.0)),
                event_type=str(ev.get("event_type", "unknown")),
                source=str(ev.get("source", "")),
                goal_id=goal_id,
                persona_id=persona_id,
                action_id=str(action_id) if action_id else None,
                evidence={"payload": payload, "source_event": "nexo.event_log"},
                metadata={"causal_parent": ev.get("causal_parent")},
            )
        )

    for idx, wt in enumerate(raw.world_trace):
        et = str(wt.get("event_type", "world.trace"))
        tick = int(wt.get("tick", 0))
        payload = _scrub_payload(dict(wt.get("payload") or {}))
        scene_id = None
        if et == "PERCEPTUAL_SCENE":
            scene_id = str(payload.get("scene_id") or f"scene-{idx}")
        normalized.append(
            CognitiveQAEvent(
                event_id=_new_id("qaev"),
                trace_id=_new_id("tr"),
                run_id=run_id,
                tick=tick,
                simulation_time=float(tick),
                event_type=f"world.{et.lower()}",
                source="browser_world",
                goal_id=goal_id,
                persona_id=persona_id,
                scene_id=scene_id,
                evidence={"payload": payload, "source_event": "world.trace_log"},
            )
        )
    normalized.sort(key=lambda e: (e.tick, e.event_id))
    return normalized
