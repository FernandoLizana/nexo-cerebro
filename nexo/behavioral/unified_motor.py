"""Motor unificado — autoridad integrada sobre legacy (Fase 12)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def summarize_unified_motor(runtime: Any) -> dict[str, Any]:
    log = runtime.state_store.event_log
    motor = [ev for ev in log if ev.event_type == "unified.motor"]
    selected = [ev for ev in log if ev.event_type == "action.selected"]
    agreements = sum(
        1 for ev in motor
        if ev.payload.get("integrated_action") == ev.payload.get("legacy_choice_key")
    )
    return {
        "motor_events": len(motor),
        "integrated_actions": len(selected),
        "motor_authority": "integrated",
        "agreement_rate": agreements / max(len(motor), 1),
        "motor_score": min(1.0, len(selected) / max(runtime.clock.tick, 1)),
    }


def export_unified_motor(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    summary = summarize_unified_motor(runtime)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "summary": summary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **summary}
