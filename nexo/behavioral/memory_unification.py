"""Métricas memory_unification — Fase 14."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def summarize_memory_unification(runtime: Any) -> dict[str, Any]:
    log = runtime.state_store.event_log
    events = [ev for ev in log if ev.event_type == "memory.unified"]
    promoted = sum(1 for ev in events if ev.payload.get("promoted"))
    return {
        "unification_events": len(events),
        "promoted_count": promoted,
        "promotion_rate": promoted / max(len(events), 1),
        "unification_score": min(1.0, promoted / max(runtime.clock.tick, 1) * 8.0),
        "mode": "post_consolidation",
    }


def export_memory_unification(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    summary = summarize_memory_unification(runtime)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "summary": summary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **summary}
