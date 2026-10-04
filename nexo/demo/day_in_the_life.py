"""Simulación acelerada 24h — timeline fenomenológica (Fase 14)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def day_in_the_life_ticks(*, simulated_hours: float = 24.0, seconds_per_tick: float = 300.0) -> int:
    """288 ticks × 300s = 86400s (24h simuladas)."""
    total_seconds = simulated_hours * 3600.0
    return max(24, int(total_seconds / seconds_per_tick))


def build_day_timeline(runtime: Any) -> dict[str, Any]:
    """Agrega fases del día desde event_log."""
    log = runtime.state_store.event_log
    sleep_phases = [ev.payload.get("phase") for ev in log if ev.event_type == "sleep.phase_changed"]
    actions = [str(ev.payload.get("action", "")) for ev in log if ev.event_type == "action.selected"]
    unified = [ev for ev in log if ev.event_type == "memory.unified" and ev.payload.get("promoted")]
    certs = [ev for ev in log if ev.event_type == "causal.certificate"]

    circadian_samples: list[dict[str, Any]] = []
    step = max(1, runtime.clock.tick // 24)
    for tick in range(step, runtime.clock.tick + 1, step):
        phase = runtime.clock.circadian_phase if tick == runtime.clock.tick else None
        circadian_samples.append({"tick": tick, "circadian_phase": phase})

    return {
        "simulated_hours": round(runtime.clock.simulation_seconds / 3600.0, 3),
        "total_ticks": runtime.clock.tick,
        "seconds_per_tick": runtime.clock.seconds_per_tick,
        "sleep_phase_changes": len(sleep_phases),
        "sleep_phases_seen": list(dict.fromkeys(sleep_phases))[-8:],
        "actions_taken": len(actions),
        "unique_actions": len(set(actions)),
        "memory_promotions": len(unified),
        "causal_certificates": len(certs),
        "circadian_end": round(runtime.clock.circadian_phase, 4),
    }


def export_day_timeline(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    timeline = build_day_timeline(runtime)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "timeline": timeline,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **timeline}
