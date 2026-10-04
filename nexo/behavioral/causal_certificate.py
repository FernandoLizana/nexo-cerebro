"""Certificado causal por tick — sesgos vs decisión (Fase 14 / H2)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _events_for_tick(log: list[Any], tick: int, event_type: str) -> list[Any]:
    return [ev for ev in log if ev.event_type == event_type and ev.tick == tick]


def _resolve_action(log: list[Any], tick: int) -> tuple[str, float, str]:
    """Acción integrada con fallback a unified.motor."""
    selected = _events_for_tick(log, tick, "action.selected")
    if selected:
        ev = selected[-1]
        action = str(ev.payload.get("action", "") or ev.payload.get("choice_key", ""))
        if action:
            source = "legacy" if ev.payload.get("legacy") else "integrated"
            return action, float(ev.payload.get("confidence", 0.0)), source

    motor = _events_for_tick(log, tick, "unified.motor")
    if motor:
        action = str(motor[-1].payload.get("integrated_action", ""))
        if action:
            return action, float(motor[-1].payload.get("confidence", 0.0)), "unified_motor"

    return "", 0.0, "none"


def build_causal_certificate(runtime: Any, *, tick: int | None = None) -> dict[str, Any]:
    """Resume evidencia causal sin seleccionar acciones."""
    log = runtime.state_store.event_log
    t = tick if tick is not None else runtime.clock.tick
    action, confidence, action_source = _resolve_action(log, t)

    motor = _events_for_tick(log, t, "unified.motor")
    bridge = _events_for_tick(log, t, "deliberation.bridge")
    guard = _events_for_tick(log, t, "autonomy.guard")
    rewards = _events_for_tick(log, t, "reward.received")

    legacy_key = ""
    agreement = False
    if motor:
        legacy_key = str(motor[-1].payload.get("legacy_choice_key", ""))
        agreement = bool(motor[-1].payload.get("agreement"))

    biases: dict[str, float] = {}
    if bridge:
        biases = dict(bridge[-1].payload.get("biases") or {})

    reward_value = float(rewards[-1].payload.get("value", 0.0)) if rewards else 0.0
    sleep_active = bool(runtime.scheduler.config.get("sleep_active"))

    certificate_valid = bool(action)
    agency_valid = bool(action) and action_source != "none"

    return {
        "tick": t,
        "integrated_action": action,
        "action_source": action_source,
        "legacy_choice_key": legacy_key,
        "motor_agreement": agreement,
        "confidence": confidence,
        "reward_value": reward_value,
        "advisory_biases": biases,
        "agency_contract": {
            "deliberation_selects_actions": True,
            "integrated_motor_primary": getattr(runtime.config, "unified_motor_mode", "legacy") == "integrated",
            "guard_events": len(guard),
            "forced_blocked": any(ev.payload.get("forced_blocked") for ev in guard),
        },
        "certificate_valid": certificate_valid,
        "agency_valid": agency_valid,
    }


def summarize_causal_certificates(runtime: Any) -> dict[str, Any]:
    log = runtime.state_store.event_log
    certs = [ev for ev in log if ev.event_type == "causal.certificate"]
    valid = sum(1 for ev in certs if ev.payload.get("certificate_valid"))
    agency_valid = sum(1 for ev in certs if ev.payload.get("agency_valid"))
    agreements = sum(1 for ev in certs if ev.payload.get("motor_agreement"))
    with_reward = sum(1 for ev in certs if float(ev.payload.get("reward_value", 0.0)) > 0.0)
    return {
        "certificate_events": len(certs),
        "valid_certificates": valid,
        "agency_valid_certificates": agency_valid,
        "motor_agreement_rate": agreements / max(len(certs), 1),
        "reward_linked_rate": with_reward / max(len(certs), 1),
        "certificate_score": min(1.0, valid / max(runtime.clock.tick, 1)),
        "agency_score": min(1.0, agency_valid / max(runtime.clock.tick, 1)),
    }


def export_causal_certificate(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    summary = summarize_causal_certificates(runtime)
    sample = build_causal_certificate(runtime)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "summary": summary,
        "sample_certificate": sample,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **summary}
