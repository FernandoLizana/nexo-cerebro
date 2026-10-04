"""Fusión deliberación integrado + legacy advisory (Sprint 35)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FUSION_POLICY = "integrated_wins"


def summarize_deliberation_fusion(runtime: Any) -> dict[str, Any]:
    log = runtime.state_store.event_log
    bridge = [ev for ev in log if ev.event_type == "deliberation.bridge"]
    fusion = [ev for ev in log if ev.event_type == "deliberation.fusion"]
    agreements = sum(1 for ev in bridge if ev.payload.get("agreement"))
    conflicts = len(bridge) - agreements
    resolved_integrated = sum(
        1 for ev in fusion if ev.payload.get("resolved_action") == ev.payload.get("integrated_action")
    )
    return {
        "fusion_policy": FUSION_POLICY,
        "bridge_events": len(bridge),
        "fusion_events": len(fusion),
        "agreements": agreements,
        "conflicts": conflicts,
        "agreement_rate": (agreements / len(bridge)) if bridge else 0.0,
        "integrated_resolutions": resolved_integrated,
        "authority": "integrated",
    }


def export_deliberation_fusion(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    summary = summarize_deliberation_fusion(runtime)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "summary": summary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **summary}
