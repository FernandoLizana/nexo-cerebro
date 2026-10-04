"""Peso configurable legacy/integrado en fusión deliberación (Sprint 43)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_LEGACY_WEIGHT = 0.0


def resolve_weighted_action(
    log: list[Any],
    *,
    tick: int,
    legacy_weight: float = DEFAULT_LEGACY_WEIGHT,
) -> dict[str, Any]:
    from nexo.behavioral.deliberation_unified import _latest_action

    weight = max(0.0, min(1.0, float(legacy_weight)))
    integrated = _latest_action(log, legacy=False, max_tick=tick)
    legacy = _latest_action(log, legacy=True, max_tick=tick)
    agreement = integrated == legacy if integrated and legacy else False
    resolved = integrated or legacy or "explore"
    policy = "integrated_wins"
    if integrated and legacy and not agreement:
        if weight >= 1.0:
            resolved = legacy
            policy = "legacy_wins"
        elif weight <= 0.0:
            resolved = integrated
            policy = "integrated_wins"
        elif weight > 0.5:
            resolved = legacy
            policy = "legacy_weighted"
        else:
            resolved = integrated
            policy = "integrated_weighted"
    return {
        "integrated_action": integrated,
        "legacy_action": legacy,
        "resolved_action": resolved,
        "agreement": agreement,
        "legacy_weight": weight,
        "fusion_policy": policy,
        "motor_authority": "weighted",
    }


def summarize_deliberation_weight(runtime: Any) -> dict[str, Any]:
    log = runtime.state_store.event_log
    weighted = [ev for ev in log if ev.event_type == "action.weighted"]
    legacy_picks = sum(
        1 for ev in weighted
        if ev.payload.get("resolved_action") == ev.payload.get("legacy_action")
        and ev.payload.get("legacy_action")
    )
    integrated_picks = sum(
        1 for ev in weighted
        if ev.payload.get("resolved_action") == ev.payload.get("integrated_action")
        and ev.payload.get("integrated_action")
    )
    return {
        "weighted_events": len(weighted),
        "legacy_picks": legacy_picks,
        "integrated_picks": integrated_picks,
        "legacy_weight": getattr(runtime.config, "legacy_advisory_weight", DEFAULT_LEGACY_WEIGHT),
        "motor_authority": "weighted",
    }


def export_deliberation_weight(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    summary = summarize_deliberation_weight(runtime)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "summary": summary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **summary}
