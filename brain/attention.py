"""
Atención competitiva: presupuesto limitado top-down vs bottom-up.

No selecciona acciones motoras. Solo ordena qué perceptos entran a WM /
deliberación. El PFC sigue eligiendo ``choice_key``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class AttentionBudget:
    """Estado del último filtro atencional."""

    budget: int = 4
    used: int = 0
    top_down_weight: float = 0.0
    bottom_up_weight: float = 0.0
    focus_source: str = ""  # top_down | bottom_up | mixed
    focus_label: str = ""
    ranked: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "budget": self.budget,
            "used": self.used,
            "top_down_weight": round(self.top_down_weight, 3),
            "bottom_up_weight": round(self.bottom_up_weight, 3),
            "focus_source": self.focus_source,
            "focus_label": self.focus_label,
            "agency_note": "Attention filters percepts only; deliberation selects actions",
        }


def _goal_match(label: str, goal: str | None, top_drive: str) -> float:
    if not label:
        return 0.0
    low = label.lower()
    score = 0.0
    if goal:
        g = goal.lower()
        if any(tok in low for tok in g.replace("(", " ").replace(")", " ").split() if len(tok) > 2):
            score += 0.55
    drive_hints = {
        "seek_food": ("hambre", "comida", "nevera", "fridge", "cosech"),
        "seek_water": ("sed", "beber", "agua"),
        "seek_rest": ("fatiga", "cama", "descans"),
        "sleep_need": ("sueño", "noche", "cama"),
        "seek_relief": ("dolor", "pain"),
        "seek_companion": ("nira", "cerca", "companion"),
        "seek_curiosity": ("escritorio", "desk", "estudi"),
        "seek_stimulus": ("tv", "tele"),
        "seek_hygiene": ("baño", "bath", "higiene"),
        "seek_bathroom": ("baño", "toilet", "vejiga"),
        "seek_warmth": ("frío", "calor"),
    }
    for hint in drive_hints.get(top_drive, ()):
        if hint in low:
            score += 0.35
            break
    return float(min(1.0, score))


def competitive_filter(
    percepts: list[dict],
    *,
    drives: dict,
    acetylcholine: float = 0.5,
    goal: str | None = None,
    budget: int = 4,
    state: AttentionBudget | None = None,
) -> tuple[list[dict], list[dict], AttentionBudget]:
    """
    Combina saliencia bottom-up con sesgo top-down (meta / drive).
    Presupuesto fijo de ítems atendidos.
    """
    st = state or AttentionBudget(budget=budget)
    st.budget = max(1, int(budget))
    if not percepts:
        st.used = 0
        st.focus_source = ""
        st.focus_label = ""
        st.ranked = []
        return [], [], st

    top_drive = max(drives.items(), key=lambda x: x[1])[0] if drives else ""
    scored: list[tuple[float, float, float, dict]] = []
    for p in percepts:
        bu = float(p.get("salience", 0.3))
        # Bottom-up boosts
        if p.get("kind") == "pain" or "dolor" in str(p.get("label", "")):
            bu = max(bu, 0.85)
        td = _goal_match(str(p.get("label", "")), goal, top_drive)
        # ACh favorece top-down (atención voluntaria)
        ach = float(np.clip(acetylcholine, 0, 1))
        w_td = 0.35 + 0.45 * ach
        w_bu = 1.0 - 0.25 * ach
        total = w_bu * bu + w_td * td
        scored.append((total, bu, td, p))

    scored.sort(key=lambda x: -x[0])
    attended_raw = scored[: st.budget]
    attended: list[dict] = []
    for total, bu, td, p in attended_raw:
        src = "bottom_up" if bu >= td + 0.08 else ("top_down" if td >= bu + 0.08 else "mixed")
        q = {**p, "attention_score": round(float(total), 3), "attention_source": src}
        attended.append(q)

    ignored = [p for _, _, _, p in scored[st.budget :]]
    st.used = len(attended)
    st.ranked = [
        {
            "label": a.get("label"),
            "score": a.get("attention_score"),
            "source": a.get("attention_source"),
        }
        for a in attended
    ]
    if attended:
        st.focus_label = str(attended[0].get("label", ""))
        st.focus_source = str(attended[0].get("attention_source", "mixed"))
        # Pesos agregados del foco
        top = next(s for s in scored if s[3] is attended_raw[0][3] or s[3].get("label") == attended[0].get("label"))
        st.bottom_up_weight = float(top[1])
        st.top_down_weight = float(top[2])
    else:
        st.focus_label = ""
        st.focus_source = ""
        st.bottom_up_weight = 0.0
        st.top_down_weight = 0.0

    return attended, ignored, st
