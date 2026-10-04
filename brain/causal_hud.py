"""
HUD causal compacto — decisión + evidencia en ~30 s de lectura.

Solo lectura: no selecciona acciones.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .mind import InfantApeBrain


def build_causal_hud(brain: InfantApeBrain) -> dict[str, Any]:
    drives = {}
    try:
        drives = brain._merged_drives()
    except Exception:
        drives = {}
    top_drive = ""
    top_val = 0.0
    if drives:
        top_drive, top_val = max(drives.items(), key=lambda item: float(item[1]))
    delib = brain.deliberation.last
    aff = brain.affordance_map.to_dict() if hasattr(brain, "affordance_map") else {}
    tel = brain.neural_telemetry.latest() if hasattr(brain, "neural_telemetry") else None
    cf = {}
    if hasattr(brain, "counterfactual") and brain.counterfactual.last_predictions:
        cf = {
            "predictions": [p.to_dict() for p in brain.counterfactual.last_predictions[:4]],
            "biases": dict(brain.counterfactual.last_biases),
        }
    contestants = []
    for c in (delib.contestants or [])[:4]:
        contestants.append(
            {
                "key": c.key,
                "label": c.label,
                "go": round(float(c.go), 3),
                "net": round(float(c.net), 3),
                "selected": bool(c.selected),
            }
        )
    return {
        "top_drive": top_drive,
        "top_drive_value": round(float(top_val), 3),
        "choice_key": delib.choice_key,
        "choice": delib.choice,
        "agency": round(float(delib.agency), 3),
        "conflict": round(float(delib.conflict), 3),
        "inhibited": bool(delib.inhibited),
        "contestants": contestants,
        "affordance_biases": dict(aff.get("last_biases") or {}),
        "affordance_records": int(aff.get("record_count") or 0),
        "last_observation": aff.get("last_observation"),
        "counterfactual": cf,
        "telemetry_tick": (tel or {}).get("tick"),
        "agency_guard": {
            "affordances_select_actions": False,
            "counterfactual_selects_actions": False,
            "telemetry_selects_actions": False,
            "hud_selects_actions": False,
            "deliberation_selects_actions": True,
            "llm_selects_actions": False,
        },
        "one_liner": (
            f"{top_drive or '—'} → {delib.choice_key or '—'} "
            f"(agency {delib.agency:.0%}, aff={int(aff.get('record_count') or 0)})"
        ),
    }
