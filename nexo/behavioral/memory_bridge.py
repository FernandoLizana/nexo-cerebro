"""Métricas memory_bridge — Fase 13."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nexo.demo.memory_bridge import sync_memory_bridge_advisory


def summarize_memory_bridge(runtime: Any) -> dict[str, Any]:
    log = runtime.state_store.event_log
    bridge = [ev for ev in log if ev.event_type == "memory.bridge"]
    parity_vals = [float(ev.payload.get("parity_ratio", 0.0)) for ev in bridge]
    avg_parity = sum(parity_vals) / max(len(parity_vals), 1)
    legacy = runtime.legacy_brain
    live = sync_memory_bridge_advisory(legacy, runtime) if legacy is not None else {}
    return {
        "bridge_events": len(bridge),
        "avg_parity_ratio": avg_parity,
        "live_parity_ratio": float(live.get("parity_ratio", 0.0)),
        "legacy_count": int(live.get("legacy_count", 0)),
        "integrated_count": int(live.get("integrated_count", 0)),
        "bridge_mode": "advisory",
        "bridge_score": min(1.0, avg_parity + 0.1 * len(bridge) / max(runtime.clock.tick, 1)),
    }


def export_memory_bridge(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    summary = summarize_memory_bridge(runtime)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "summary": summary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **summary}
