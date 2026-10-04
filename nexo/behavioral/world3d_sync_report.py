"""Reportes sincronización World3D (Sprint 56)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nexo.demo.world3d_sync import compare_with_legacy, extract_game3d_state, game3d_fidelity_score


def summarize_world3d_sync(runtime: Any) -> dict[str, Any]:
    world = runtime.world
    state = extract_game3d_state(world) if hasattr(world, "game3d_state") else extract_game3d_state(world)
    fidelity = game3d_fidelity_score(state)
    legacy_cmp: dict[str, Any] = {}
    if runtime.legacy_brain is not None and hasattr(runtime.legacy_brain, "_world_dict"):
        try:
            legacy_cmp = compare_with_legacy(state, runtime.legacy_brain._world_dict())
        except Exception as exc:
            legacy_cmp = {"error": str(exc)}
    log = runtime.state_store.event_log
    sync_events = [ev for ev in log if ev.event_type == "world3d.sync"]
    return {
        "fidelity": fidelity,
        "furniture_count": len(state.get("furniture") or []),
        "room": state.get("room"),
        "sync_events": len(sync_events),
        "legacy_comparison": legacy_cmp,
        "sync_score": legacy_cmp.get("sync_score", fidelity),
    }


def export_world3d_sync(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    summary = summarize_world3d_sync(runtime)
    state = extract_game3d_state(runtime.world)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "game3d_state_keys": sorted(state.keys()),
        "summary": summary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **summary}
