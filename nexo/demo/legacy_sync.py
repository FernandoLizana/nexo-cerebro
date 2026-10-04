"""Sincronización legacy ↔ integrado (Fase 12)."""

from __future__ import annotations

from typing import Any


def sync_legacy_deliberation_from_integrated(brain: Any, runtime: Any) -> dict[str, Any]:
    """Copia última acción integrada al HUD/deliberación legacy."""
    log = runtime.state_store.event_log
    selected = [ev for ev in log if ev.event_type == "action.selected"]
    if not selected:
        return {"synced": False}
    last = selected[-1]
    key = str(last.payload.get("action") or "explore")
    agency = float(last.payload.get("confidence", 0.5))
    delib = brain.deliberation.last
    delib.choice_key = key
    delib.agency = agency
    delib.choice = key
    return {"synced": True, "choice_key": key, "agency": agency}


def sync_legacy_body_from_integrated(brain: Any, runtime: Any) -> dict[str, Any]:
    """Copia homeostasis integrada al cuerpo legacy."""
    ib = runtime.body
    lb = brain.body
    synced: list[str] = []
    for attr in ("energy", "fatigue", "hydration", "sleep_pressure", "pain", "temperature"):
        if hasattr(ib, attr) and hasattr(lb, attr):
            setattr(lb, attr, float(getattr(ib, attr)))
            synced.append(attr)
    return {"synced_fields": synced}


def sync_integrated_body_from_legacy(brain: Any, runtime: Any) -> None:
    lb = brain.body
    ib = runtime.body
    for attr in ("energy", "fatigue", "hydration", "sleep_pressure"):
        if hasattr(lb, attr) and hasattr(ib, attr):
            setattr(ib, attr, float(getattr(lb, attr)))
