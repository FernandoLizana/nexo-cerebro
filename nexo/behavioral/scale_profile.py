"""Perfil de escala computacional del runtime integrado (Sprint 29)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def collect_scale_metrics(runtime: Any, result: dict[str, Any]) -> dict[str, Any]:
    ticks = max(int(result.get("ticks", 0)), 1)
    event_count = int(result.get("event_count", 0))
    graph = runtime.scheduler.router.graph
    enabled = sum(1 for reg in runtime.scheduler.processes if reg.enabled)
    return {
        "ticks": ticks,
        "event_count": event_count,
        "events_per_tick": round(event_count / ticks, 4),
        "connectome_modules": len(getattr(graph, "modules", {}) or {}),
        "connectome_connections": len(getattr(graph, "connections", []) or []),
        "registered_processes": len(runtime.scheduler.processes),
        "enabled_processes": enabled,
        "trace_events": int(result.get("trace_events", 0)),
        "memory_retrievals": int(result.get("memory_retrievals", 0)),
        "world_mode": getattr(runtime.config, "world_mode", "room"),
    }


def export_scale_profile(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
    *,
    elapsed_seconds: float | None = None,
) -> dict[str, Any]:
    metrics = collect_scale_metrics(runtime, result)
    if elapsed_seconds is not None and elapsed_seconds > 0:
        metrics["ticks_per_second"] = round(metrics["ticks"] / elapsed_seconds, 4)
        metrics["elapsed_seconds"] = round(elapsed_seconds, 4)
    payload = {"profile": result.get("profile"), "seed": result.get("seed"), "metrics": metrics}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), "metrics": metrics}


def benchmark_runtime_ticks(
    runtime: Any,
    ticks: int,
) -> dict[str, Any]:
    """Mide ticks/segundo sin exportar archivos."""
    start = time.perf_counter()
    result = runtime.run(ticks)
    elapsed = time.perf_counter() - start
    metrics = collect_scale_metrics(runtime, result)
    metrics["elapsed_seconds"] = round(elapsed, 4)
    metrics["ticks_per_second"] = round(ticks / elapsed, 4) if elapsed > 0 else 0.0
    return {"result": result, "metrics": metrics}
