"""Puente roadmap100 legacy → runtime integrado (Sprint 53)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def count_roadmap100_flags(flags: Any) -> dict[str, Any]:
    try:
        from nexo.experiment_conditions import ROADMAP100_V1_ENABLED_FLAGS
        from dataclasses import asdict

        data = asdict(flags) if hasattr(flags, "__dataclass_fields__") else {}
        enabled = [k for k in ROADMAP100_V1_ENABLED_FLAGS if data.get(k)]
        return {
            "catalog_size": len(ROADMAP100_V1_ENABLED_FLAGS),
            "enabled_count": len(enabled),
            "coverage": len(enabled) / max(len(ROADMAP100_V1_ENABLED_FLAGS), 1),
            "enabled_sample": enabled[:12],
        }
    except Exception as exc:
        return {"catalog_size": 0, "enabled_count": 0, "coverage": 0.0, "error": str(exc)}


def summarize_roadmap100_bridge(runtime: Any) -> dict[str, Any]:
    log = runtime.state_store.event_log
    bridge = [ev for ev in log if ev.event_type == "roadmap100.bridge"]
    legacy = runtime.legacy_brain
    flag_info: dict[str, Any] = {}
    if legacy is not None:
        flag_info = count_roadmap100_flags(getattr(legacy, "experiment_flags", None))
    stacks = []
    if legacy is not None:
        for name in (
            "executive", "memory_dynamics", "affect_dynamics",
            "language_dynamics", "motor_dynamics", "lifecycle_dynamics",
        ):
            if hasattr(legacy, name):
                stacks.append(name)
    return {
        "bridge_events": len(bridge),
        "legacy_stacks_present": stacks,
        "roadmap100_flags": flag_info,
        "bridge_mode": "advisory",
    }


def export_roadmap100_bridge(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    summary = summarize_roadmap100_bridge(runtime)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "summary": summary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **summary}
