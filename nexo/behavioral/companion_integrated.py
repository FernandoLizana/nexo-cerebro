"""Compañera Nira integrada — dyad advisory (Sprint 58)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class IntegratedCompanionState:
    name: str = "Nira"
    x: float = 280.0
    y: float = 230.0
    agent_dir: int = -1
    bond: float = 0.42
    dyad_events: int = 0
    proximity_ticks: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "x": round(self.x, 1),
            "y": round(self.y, 1),
            "dir": self.agent_dir,
            "bond": round(self.bond, 3),
            "dyad_events": self.dyad_events,
            "proximity_ticks": self.proximity_ticks,
        }


def companion_from_legacy(runtime: Any) -> IntegratedCompanionState | None:
    legacy = runtime.legacy_brain
    if legacy is None:
        return None
    comp = getattr(legacy, "companion", None)
    if comp is None:
        return IntegratedCompanionState()
    return IntegratedCompanionState(
        name=str(getattr(comp, "name", "Nira")),
        x=float(getattr(comp, "x", 280.0)),
        y=float(getattr(comp, "y", 230.0)),
        agent_dir=int(getattr(comp, "agent_dir", -1)),
        bond=float(getattr(comp, "bond_with_nexo", 0.42)),
    )


def summarize_companion_integrated(runtime: Any) -> dict[str, Any]:
    log = runtime.state_store.event_log
    dyad = [ev for ev in log if ev.event_type == "companion.dyad"]
    state = runtime.scheduler.config.get("companion_state")
    if state is None:
        state = companion_from_legacy(runtime) or IntegratedCompanionState()
    prox = state.proximity_ticks if isinstance(state, IntegratedCompanionState) else 0
    return {
        "companion_name": state.name if isinstance(state, IntegratedCompanionState) else "Nira",
        "bond": state.bond if isinstance(state, IntegratedCompanionState) else 0.42,
        "dyad_events": len(dyad),
        "proximity_ticks": prox,
        "legacy_companion_present": runtime.legacy_brain is not None and hasattr(runtime.legacy_brain, "companion"),
        "dyad_score": min(1.0, len(dyad) / max(runtime.clock.tick, 1) * 2 + (state.bond if isinstance(state, IntegratedCompanionState) else 0) * 0.4),
    }


def export_companion_integrated(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    summary = summarize_companion_integrated(runtime)
    state = runtime.scheduler.config.get("companion_state")
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "companion": state.to_dict() if hasattr(state, "to_dict") else {},
        "summary": summary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **summary}
