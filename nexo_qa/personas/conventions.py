"""Digital literacy UI conventions — generic priors, not site-specific."""

from __future__ import annotations

import re

# Configurable convention table: pattern → semantic hint weight at full literacy
UI_CONVENTIONS: tuple[tuple[str, str, float], ...] = (
    (r"☰|≡|menu|hamburg", "navigation_menu", 0.35),
    (r"⚙|gear|settings|ajustes|configuraci", "settings", 0.3),
    (r"🔍|search|buscar|magnif", "search", 0.28),
    (r"breadcrumb|miga|ruta", "navigation_path", 0.22),
    (r"cancel|cancelar", "cancel_action", 0.25),
    (r"confirm|confirmar|aceptar", "confirm_action", 0.2),
    (r"review|revisar|ver detalle", "review_action", 0.18),
)


def convention_relevance_boost(digital_literacy: float, label: str) -> float:
    """Scale generic UI convention confidence by literacy trait."""
    if not label:
        return 0.0
    text = label.lower()
    literacy = max(0.0, min(1.0, float(digital_literacy)))
    boost = 0.0
    for pattern, _hint, weight in UI_CONVENTIONS:
        if re.search(pattern, text, re.IGNORECASE):
            boost = max(boost, weight * literacy)
    return float(boost)
