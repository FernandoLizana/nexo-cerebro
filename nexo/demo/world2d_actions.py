"""Mapeo choice_key legacy → acciones integradas (Sprint 32, catálogo completo Sprint 36)."""

from __future__ import annotations

LEGACY_TO_INTEGRATED: dict[str, str] = {
    "eat": "eat",
    "cook": "eat",
    "harvest": "eat",
    "drink": "rest",
    "rest": "rest",
    "sleep": "rest",
    "tv": "inspect_distractor",
    "research": "explore",
    "study": "explore",
    "wander": "explore",
    "explore": "explore",
    "flee": "flee",
    "approach_caregiver": "approach_caregiver",
    "social": "approach_caregiver",
}

FULL_LEGACY_CATALOG: dict[str, str] = {
    **LEGACY_TO_INTEGRATED,
    "clinical": "explore",
    "biopsych": "explore",
    "infant": "explore",
    "hygiene": "rest",
    "bathroom": "rest",
    "companion": "approach_caregiver",
    "warmth": "rest",
    "relief": "rest",
}


def map_legacy_action(choice_key: str, *, full: bool = False) -> str:
    key = (choice_key or "").strip().lower()
    table = FULL_LEGACY_CATALOG if full else LEGACY_TO_INTEGRATED
    return table.get(key, "explore")


def mapping_coverage(
    keys: tuple[str, ...] | list[str],
    *,
    full: bool = False,
) -> dict[str, str | None]:
    table = FULL_LEGACY_CATALOG if full else LEGACY_TO_INTEGRATED
    return {k: table.get(k.strip().lower()) for k in keys}


def full_catalog_coverage() -> float:
    """Fracción de claves CHOICE_EVENT_MAP legacy con mapeo explícito."""
    try:
        from brain.behavior_integration import CHOICE_EVENT_MAP

        keys = tuple(CHOICE_EVENT_MAP.keys())
    except ImportError:
        keys = tuple(FULL_LEGACY_CATALOG.keys())
    if not keys:
        return 0.0
    mapped = sum(1 for k in keys if k in FULL_LEGACY_CATALOG)
    return mapped / len(keys)
