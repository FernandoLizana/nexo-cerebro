"""Legacy string actions → ActionSchema (adapter boundary, not PFC)."""

from __future__ import annotations

from typing import Any, Mapping

from nexo.core.action_schema import ActionSchema

# Historical RoomWorld catalog — kept here so cognition does not own it.
# Import alias `ROOM_ACTION_SCHEMAS` remains for existing callers.
ROOM_ACTION_SCHEMAS: tuple[dict[str, str], ...] = (
    {"key": "eat", "drive": "hunger", "label": "comer"},
    {"key": "rest", "drive": "rest", "label": "descansar"},
    {"key": "flee", "drive": "safety", "label": "huir"},
    {"key": "approach_caregiver", "drive": "social", "label": "acercarse al cuidador"},
    {"key": "explore", "drive": "curiosity", "label": "explorar"},
    {"key": "inspect_distractor", "drive": "curiosity", "label": "inspeccionar distractor"},
)

_BY_KEY = {row["key"]: row for row in ROOM_ACTION_SCHEMAS}

_AFFORDANCE_BY_KEY = {
    "eat": "consumable",
    "rest": "restorable",
    "flee": "avoidable",
    "approach_caregiver": "approachable",
    "explore": "navigable",
    "inspect_distractor": "inspectable",
}

_TYPE_BY_KEY = {
    "eat": "consume",
    "rest": "recover",
    "flee": "avoid",
    "approach_caregiver": "social",
    "explore": "explore",
    "inspect_distractor": "inspect",
}

_TARGET_BY_KEY = {
    "eat": "food_source",
    "rest": "self",
    "flee": "safe_zone",
    "approach_caregiver": "caregiver",
    "explore": "environment",
    "inspect_distractor": "distractor",
}

_AFFORDANCE_BY_MODALITY = {
    "food": "consumable",
    "interoception": "restorable",
    "danger": "avoidable",
    "caregiver": "approachable",
    "distractor": "inspectable",
    "spatial": "navigable",
}

_DRIVE_BY_AFFORDANCE = {
    "consumable": "hunger",
    "restorable": "rest",
    "avoidable": "safety",
    "approachable": "social",
    "navigable": "curiosity",
    "inspectable": "curiosity",
}


def drive_for_affordance(affordance: str | None) -> str:
    if not affordance:
        return ""
    return _DRIVE_BY_AFFORDANCE.get(affordance, "")


def schema_from_legacy_action(
    action_id: str,
    info: Mapping[str, Any] | None = None,
) -> ActionSchema:
    """Deterministic, reversible (id stays the legacy verb)."""
    info = dict(info or {})
    known = _BY_KEY.get(action_id)
    modality = str(info.get("modality") or "")
    affordance = _AFFORDANCE_BY_KEY.get(action_id) or _AFFORDANCE_BY_MODALITY.get(modality)
    label = known["label"] if known else action_id.replace("_", " ")
    cost = info.get("cost_energy")
    risk = info.get("risk")
    return ActionSchema(
        id=str(action_id),
        label=str(label),
        action_type=_TYPE_BY_KEY.get(action_id, "act"),
        target=_TARGET_BY_KEY.get(action_id) or (modality or None),
        affordance=affordance,
        expected_effect=known["drive"] if known else drive_for_affordance(affordance) or None,
        estimated_cost=None if cost is None else float(cost),
        risk=None if risk is None else float(risk),
        metadata={"source": "legacy_adapter", "modality": modality},
    )


def schemas_from_action_catalog(
    action_ids: tuple[str, ...] | list[str],
    infos: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[ActionSchema, ...]:
    infos = infos or {}
    return tuple(schema_from_legacy_action(action_id, infos.get(action_id)) for action_id in action_ids)


def legacy_id_from_schema(schema: ActionSchema) -> str:
    return schema.id
