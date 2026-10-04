"""Deliberación unificada — fusión afecta acción motora (Sprint 39)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nexo.behavioral.deliberation_fusion import FUSION_POLICY


def _latest_action(log: list[Any], *, legacy: bool | None = None, max_tick: int | None = None) -> str | None:
    for ev in reversed(log):
        if ev.event_type != "action.selected":
            continue
        is_legacy = bool(ev.payload.get("legacy"))
        if legacy is True and not is_legacy:
            continue
        if legacy is False and is_legacy:
            continue
        if max_tick is not None and ev.tick > max_tick:
            continue
        action = ev.payload.get("action")
        if action:
            return str(action)
    return None


def resolve_unified_action(
    log: list[Any],
    *,
    tick: int,
) -> dict[str, Any]:
    integrated = _latest_action(log, legacy=False, max_tick=tick)
    legacy = _latest_action(log, legacy=True, max_tick=tick)
    agreement = integrated == legacy if integrated and legacy else False
    resolved = integrated or legacy or "explore"
    if integrated and legacy and not agreement:
        resolved = integrated  # integrated_wins
    return {
        "integrated_action": integrated,
        "legacy_action": legacy,
        "resolved_action": resolved,
        "agreement": agreement,
        "fusion_policy": FUSION_POLICY,
        "motor_authority": "unified",
    }


def summarize_deliberation_unified(runtime: Any) -> dict[str, Any]:
    log = runtime.state_store.event_log
    unified = [ev for ev in log if ev.event_type == "action.unified"]
    overrides = sum(
        1 for ev in unified
        if ev.payload.get("integrated_action") != ev.payload.get("legacy_action")
        and ev.payload.get("legacy_action")
    )
    agreements = sum(1 for ev in unified if ev.payload.get("agreement"))
    return {
        "unified_events": len(unified),
        "motor_overrides": overrides,
        "agreements": agreements,
        "agreement_rate": (agreements / len(unified)) if unified else 0.0,
        "fusion_policy": FUSION_POLICY,
        "motor_authority": "unified",
    }


def export_deliberation_unified(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    summary = summarize_deliberation_unified(runtime)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "summary": summary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **summary}
