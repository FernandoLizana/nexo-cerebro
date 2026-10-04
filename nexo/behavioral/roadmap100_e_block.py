"""Auditoría bloque E roadmap100 / legacy E1–E8 (Fase 13)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROADMAP100_E_BLOCK_IDS: tuple[str, ...] = (
    "baseline_legacy",
    "legacy_no_binding",
    "legacy_no_pfc",
    "roadmap100_no_hippocampus_v1",
    "roadmap100_no_affect_v1",
    "roadmap100_no_consciousness_v1",
    "roadmap100_full_v1",
    "roadmap100_safe_v1",
)


def audit_e_block_conditions() -> dict[str, Any]:
    from nexo.experiment_conditions import get_condition

    resolved: list[str] = []
    errors: list[str] = []
    for cid in ROADMAP100_E_BLOCK_IDS:
        try:
            cond = get_condition(cid)
            resolved.append(cond.condition_id)
        except Exception as exc:
            errors.append(f"{cid}: {exc}")
    return {
        "catalog_size": len(ROADMAP100_E_BLOCK_IDS),
        "resolved_count": len(resolved),
        "coverage": len(resolved) / max(len(ROADMAP100_E_BLOCK_IDS), 1),
        "resolved": resolved,
        "errors": errors,
    }


def summarize_roadmap100_e_block(runtime: Any) -> dict[str, Any]:
    log = runtime.state_store.event_log
    events = [ev for ev in log if ev.event_type == "roadmap100.e_block"]
    audit = audit_e_block_conditions()
    last_cov = float(events[-1].payload.get("coverage", 0.0)) if events else audit["coverage"]
    return {
        "e_block_events": len(events),
        "condition_coverage": last_cov,
        "catalog_size": audit["catalog_size"],
        "resolved_count": audit["resolved_count"],
        "e_block_score": min(1.0, last_cov),
    }


def export_roadmap100_e_block(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    summary = summarize_roadmap100_e_block(runtime)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "conditions": audit_e_block_conditions(),
        "summary": summary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **summary}
