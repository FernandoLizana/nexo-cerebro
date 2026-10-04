"""Puente Flask demo ↔ runtime integrado (Sprint 55)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FLASK_API_PARITY_CHECKLIST: tuple[str, ...] = (
    "GET /api/world",
    "POST /api/world/tick",
    "GET /api/neural/causal/hud",
    "GET /api/neural/observatory",
    "GET /api/time",
)


def build_flask_bridge_payload(runtime: Any) -> dict[str, Any]:
    """Payload mínimo compatible con rutas Flask demo."""
    world = runtime.world
    legacy = runtime.legacy_brain
    agent = {"x": 0.0, "y": 0.0, "dir": 1}
    room = "unknown"
    furniture_n = 0
    if hasattr(world, "_world2d") and world._world2d is not None:
        w2 = world._world2d
        agent = {
            "x": round(float(w2.agent_x), 1),
            "y": round(float(w2.agent_y), 1),
            "dir": int(w2.agent_dir),
        }
        room = w2.current_room() if hasattr(w2, "current_room") else room
        furniture_n = len(getattr(w2, "furniture", []))
    elif hasattr(world, "agent_x"):
        agent = {"x": round(float(world.agent_x), 1), "y": 0.0, "dir": 1}
    legacy_ready = legacy is not None
    hud_ready = legacy_ready and hasattr(legacy, "deliberation")
    return {
        "bridge_mode": "integrated",
        "profile": runtime.config.profile,
        "agent": agent,
        "room": room,
        "furniture_count": furniture_n,
        "legacy_brain_attached": legacy_ready,
        "hud_ready": hud_ready,
        "api_parity_checklist": list(FLASK_API_PARITY_CHECKLIST),
        "ticks": runtime.clock.tick,
    }


def summarize_flask_demo_bridge(runtime: Any) -> dict[str, Any]:
    log = runtime.state_store.event_log
    bridge = [ev for ev in log if ev.event_type == "flask.bridge"]
    payload = build_flask_bridge_payload(runtime)
    return {
        "bridge_events": len(bridge),
        "legacy_brain_attached": payload["legacy_brain_attached"],
        "hud_ready": payload["hud_ready"],
        "furniture_count": payload["furniture_count"],
        "api_parity_size": len(FLASK_API_PARITY_CHECKLIST),
        "bridge_score": min(
            1.0,
            (0.4 if payload["legacy_brain_attached"] else 0.0)
            + (0.3 if payload["hud_ready"] else 0.0)
            + min(0.3, payload["furniture_count"] / 12.0),
        ),
    }


def export_flask_demo_bridge(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    summary = summarize_flask_demo_bridge(runtime)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "bridge_payload": build_flask_bridge_payload(runtime),
        "summary": summary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **summary}
