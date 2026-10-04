"""Adaptador legacy temprano — corre antes del BG integrado (Sprint 51)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def summarize_legacy_adapter_early(runtime: Any) -> dict[str, Any]:
    log = runtime.state_store.event_log
    legacy = [
        ev for ev in log
        if ev.event_type == "action.selected" and ev.payload.get("legacy")
    ]
    integrated = [
        ev for ev in log
        if ev.event_type == "action.selected" and not ev.payload.get("legacy")
    ]
    same_tick = 0
    legacy_by_tick: dict[int, list] = {}
    for ev in legacy:
        legacy_by_tick.setdefault(ev.tick, []).append(ev)
    for ev in integrated:
        if ev.tick in legacy_by_tick:
            same_tick += 1
    return {
        "early_adapter": True,
        "legacy_adapter_priority": 61,
        "legacy_action_events": len(legacy),
        "integrated_action_events": len(integrated),
        "same_tick_pairs": same_tick,
        "timing_authority": "legacy_first",
    }


def export_legacy_adapter_early(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    summary = summarize_legacy_adapter_early(runtime)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "summary": summary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **summary}
