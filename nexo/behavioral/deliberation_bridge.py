"""Auditoría puente deliberación integrado vs legacy (Sprint 31)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def summarize_deliberation_bridge(runtime: Any) -> dict[str, Any]:
    log = runtime.state_store.event_log
    bridge_events = [ev for ev in log if ev.event_type == "deliberation.bridge"]
    integrated = [
        ev for ev in log
        if ev.event_type == "action.selected" and not ev.payload.get("legacy")
    ]
    legacy = [
        ev for ev in log
        if ev.event_type == "action.selected" and ev.payload.get("legacy")
    ]
    agreements = sum(
        1 for ev in bridge_events
        if ev.payload.get("integrated_action") == ev.payload.get("legacy_action")
    )
    return {
        "bridge_events": len(bridge_events),
        "integrated_selections": len(integrated),
        "legacy_selections": len(legacy),
        "bridge_agreements": agreements,
        "authority": "integrated",
    }


def export_deliberation_bridge(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "summary": summarize_deliberation_bridge(runtime),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **payload["summary"]}
