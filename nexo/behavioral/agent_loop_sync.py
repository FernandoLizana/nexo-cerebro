"""Métricas agent_loop_sync — Fase 13."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def summarize_agent_loop_sync(runtime: Any) -> dict[str, Any]:
    log = runtime.state_store.event_log
    sync_events = [ev for ev in log if ev.event_type == "agent_loop.sync"]
    lite_runs = sum(1 for ev in sync_events if ev.payload.get("lite_sync"))
    return {
        "sync_events": len(sync_events),
        "lite_sync_runs": lite_runs,
        "sync_score": min(1.0, lite_runs / max(runtime.clock.tick, 1)),
        "mode": "lite_post_tick",
    }


def export_agent_loop_sync(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    summary = summarize_agent_loop_sync(runtime)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "summary": summary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **summary}
