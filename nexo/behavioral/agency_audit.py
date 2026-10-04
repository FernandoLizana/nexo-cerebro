"""Auditoría agency — certificados causales + contrato autonomía (Fase 15 / H2)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nexo.behavioral.causal_certificate import summarize_causal_certificates


def summarize_agency_audit(runtime: Any) -> dict[str, Any]:
    causal = summarize_causal_certificates(runtime)
    log = runtime.state_store.event_log
    guard = [ev for ev in log if ev.event_type == "autonomy.guard"]
    audits = [ev for ev in log if ev.event_type == "agency.audit"]
    forced = sum(1 for ev in guard if ev.payload.get("forced_blocked"))
    return {
        "audit_events": len(audits),
        "guard_events": len(guard),
        "forced_blocked_count": forced,
        "agency_score": causal.get("agency_score", 0.0),
        "certificate_score": causal.get("certificate_score", 0.0),
        "agency_valid_certificates": causal.get("agency_valid_certificates", 0),
        "valid_certificates": causal.get("valid_certificates", 0),
        "motor_agreement_rate": causal.get("motor_agreement_rate", 0.0),
        "deliberation_selects_actions": True,
        "audit_mode": "causal_certificate_v2",
    }


def export_agency_audit(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    summary = summarize_agency_audit(runtime)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "summary": summary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **summary}
