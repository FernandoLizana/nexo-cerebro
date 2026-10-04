"""
Señales internas para la corteza del lenguaje — hechos neuroquímicos, no diálogo.
"""

from __future__ import annotations

import json
from typing import Any


def state_packet(
    *,
    ep: dict,
    body: dict,
    room: str,
    world: dict,
    motor: list[int],
    thought: str | None = None,
    thought_packet: dict | None = None,
    event: dict | None = None,
    working_memory: list[dict] | None = None,
    current_goal: str | None = None,
    companion_present: bool = False,
    modulators: dict | None = None,
    chemistry: dict | None = None,
    cortical: dict | None = None,
    consciousness: dict | None = None,
) -> str:
    """Borrador factual que Broca/Ollama traduce; no es lo que Nexo dice al usuario."""
    hypo = ep.get("hypothalamus", {})
    packet: dict[str, Any] = {
        "room": room,
        "motor_pattern": motor,
        "mood": hypo.get("mood"),
        "valence": round(float(ep.get("valence", 0)), 3),
        "arousal": round(float(ep.get("arousal", 0)), 3),
        "remembered": bool(ep.get("remembered")),
        "body": body,
        "visible": world.get("visible", [])[:5],
        "tv": world.get("tv"),
        "dominant_drive": current_goal or _dominant_drive(body.get("drives", {})),
        "hypothalamus": {
            "oxytocin": round(float(hypo.get("oxytocin", 0)), 3),
            "cortisol": round(float(hypo.get("cortisol", 0)), 3),
            "dopamine": round(float(hypo.get("dopamine", 0)), 3),
            "energy": round(float(hypo.get("energy", 0)), 3),
        },
    }
    if modulators:
        packet["neuromodulators"] = modulators
    if chemistry:
        packet["pair_bond"] = chemistry
    if cortical:
        packet["cortical"] = cortical
    if working_memory:
        packet["working_memory"] = working_memory[:7]
    if companion_present:
        packet["companion_near"] = True
    if thought_packet:
        packet["thought_neural"] = thought_packet
    elif thought:
        packet["inner_thought"] = thought
    if event:
        packet["last_event"] = event
    prior = ep.get("prior")
    if prior:
        packet["memory_echo"] = prior.get("label")
    if consciousness:
        packet["conscious_moment"] = consciousness.get("winner") or {}
        packet["metacognition"] = consciousness.get("metacognition") or {}
        if consciousness.get("self"):
            packet["self_model"] = consciousness["self"]
    return json.dumps(packet, ensure_ascii=False)


def _dominant_drive(drives: dict) -> str | None:
    if not drives:
        return None
    best = max(drives.items(), key=lambda x: x[1])
    return best[0] if best[1] > 0.25 else None
