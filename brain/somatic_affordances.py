"""
Contacto somático con el entorno — el mueble modifica interocepción; nadie «manda» sentarse.

El sofá no es un objetivo de navegación: si Nexo está sobre él, el confort sube y eso puede
inclinar impulsos internos (seek_rest, confort) sin script de comportamiento.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .body import BodyState
    from .world import Furniture, World2D

# Efectos por tick de contacto (solo mientras hay solapamiento corporal)
CONTACT_EFFECTS: dict[str, dict[str, float]] = {
    "sofa": {"comfort": 0.045, "fatigue": -0.018, "pain_limbs": -0.012},
    "bed": {"comfort": 0.035, "fatigue": -0.035, "pain_limbs": -0.008},
    "bath": {"comfort": 0.025, "hygiene": -0.02, "body_temp": 0.015},
    "desk": {"comfort": -0.008, "fatigue": 0.004},
    "fridge": {"body_temp": -0.006},
    "tv": {"comfort": 0.012, "pleasure": 0.008, "fatigue": 0.003},
    "stove": {"body_temp": 0.018, "comfort": 0.006},
    "chair": {"comfort": 0.022, "fatigue": -0.01},
}


def furniture_contact(world: World2D, *, pad: float = 14.0) -> Furniture | None:
    """Contacto corporal amplio (no colisión dura de pathfinding)."""
    ax, ay = world.agent_x, world.agent_y
    best, best_d = None, 1e9
    for fu in world.furniture:
        if fu.kind == "door":
            continue
        cx = fu.x + fu.w / 2
        cy = fu.y + fu.h / 2
        if fu.x - pad <= ax <= fu.x + fu.w + pad and fu.y - pad <= ay <= fu.y + fu.h + pad:
            d = float(np.hypot(ax - cx, ay - cy))
            if d < best_d:
                best_d, best = d, fu
    return best


def apply_somatic_contact(
    world: World2D,
    body: BodyState,
    *,
    nociceptor=None,
) -> dict[str, Any] | None:
    fu = furniture_contact(world)
    if not fu:
        return None
    effects = CONTACT_EFFECTS.get(fu.kind, {})
    if not effects:
        return None

    for key, delta in effects.items():
        if not hasattr(body, key):
            continue
        cur = float(getattr(body, key))
        setattr(body, key, float(np.clip(cur + delta, 0, 1)))

    if nociceptor and effects.get("pain_limbs", 0) < 0:
        nociceptor.gate_inhibition(abs(effects["pain_limbs"]) * 2.8, regions=("limbs", "torso"))
        nociceptor._project_to_body(body)

    return {
        "kind": fu.kind,
        "label": fu.label,
        "effects": {k: round(v, 4) for k, v in effects.items()},
    }
