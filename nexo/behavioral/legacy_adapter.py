"""Telemetría del adaptador legacy en runtime integrado (Sprint 27)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def summarize_legacy_adapter(runtime: Any) -> dict[str, Any]:
    log = runtime.state_store.event_log
    legacy_events = [
        ev for ev in log
        if ev.source == "legacy_brain_adapter"
    ]
    legacy_actions = [
        ev for ev in log
        if ev.event_type == "action.selected" and ev.payload.get("legacy")
    ]
    integrated_actions = [
        ev for ev in log
        if ev.event_type == "action.selected" and not ev.payload.get("legacy")
    ]
    return {
        "legacy_adapter_active": runtime.legacy_brain is not None,
        "use_legacy_adapter": runtime.config.use_legacy_adapter,
        "legacy_adapter_events": len(legacy_events),
        "legacy_action_events": len(legacy_actions),
        "integrated_action_events": len(integrated_actions),
        "legacy_unique_actions": sorted({
            str(ev.payload.get("action", ""))
            for ev in legacy_actions
            if ev.payload.get("action")
        }),
    }


def export_legacy_adapter_report(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "summary": summarize_legacy_adapter(runtime),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **payload["summary"]}
