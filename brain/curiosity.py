"""
Drive de curiosidad: exploración autónoma hacia lo desconocido (símbolos, libros, estímulos).
"""

from __future__ import annotations

import numpy as np

from .body import BodyState
from .neurotransmitters import NeuromodulatorState

ARCHETYPE_CARD_TOUCH_THRESHOLD = 0.38
ARCHETYPE_CARD_RETOUCH_THRESHOLD = 0.72
BOOK_READ_THRESHOLD = 0.32


def compute_curiosity(
    body: BodyState,
    mods: NeuromodulatorState,
    *,
    unseen_cards: int = 0,
    internalized_cards: int = 0,
    sleep_pressure: float = 0.0,
    valence: float = 0.0,
    unread_shelf: int = 0,
) -> float:
    """Impulso 0–1 hacia explorar e interiorizar."""
    pain = body.total_pain()
    base = (
        0.18
        + 0.32 * mods.dopamine
        + 0.15 * body.drives().get("seek_stimulus", 0)
        + 0.08 * min(unseen_cards, 5) / 5.0
        + 0.08 * min(int(unread_shelf), 1)
        - 0.35 * pain
        - 0.28 * sleep_pressure
        - 0.12 * body.fatigue
        + 0.06 * max(valence, 0)
    )
    if internalized_cards > 12:
        base *= 0.85
    return float(np.clip(base, 0, 1))


def curiosity_drives(
    body: BodyState,
    mods: NeuromodulatorState,
    *,
    unseen_cards: int = 0,
    internalized_cards: int = 0,
    sleep_pressure: float = 0.0,
    valence: float = 0.0,
    unread_shelf: int = 0,
) -> dict[str, float]:
    drives = body.drives()
    drives["seek_curiosity"] = compute_curiosity(
        body,
        mods,
        unseen_cards=unseen_cards,
        internalized_cards=internalized_cards,
        sleep_pressure=sleep_pressure,
        valence=valence,
        unread_shelf=unread_shelf,
    )
    return drives
