"""Human event normalization — semantic categories, no CSS/XPath identity."""

from __future__ import annotations

import re
from typing import Any

from nexo_qa.human_lab.models import HumanActionCategory, HumanInteractionEvent

FORBIDDEN_IDENTITY_KEYS = ("css", "xpath", "selector", "data-testid", "dom_path")

CATEGORY_MAP: dict[str, HumanActionCategory] = {
    "click": "ACTIVATE",
    "activate": "ACTIVATE",
    "submit": "ACTIVATE",
    "type": "TYPE",
    "input": "TYPE",
    "select": "SELECT",
    "toggle": "TOGGLE",
    "scroll": "SCROLL",
    "back": "BACK",
    "wait": "WAIT",
    "abandon": "ABANDON",
}


def infer_action_category(raw_type: str, semantic_target: str = "") -> HumanActionCategory:
    key = raw_type.lower().strip()
    if key in CATEGORY_MAP:
        return CATEGORY_MAP[key]
    combined = f"{key} {semantic_target.lower()}"
    for token, cat in CATEGORY_MAP.items():
        if token in combined:
            return cat
    return "OTHER"


def normalize_human_event(raw: dict[str, Any]) -> HumanInteractionEvent:
    meta = dict(raw.get("metadata") or {})
    for k in list(meta.keys()):
        if any(f in k.lower() for f in FORBIDDEN_IDENTITY_KEYS):
            meta.pop(k, None)
    event_type = str(raw.get("event_type", "interaction"))
    semantic = str(raw.get("semantic_target", raw.get("target_label", "")))
    category = raw.get("action_category")
    if not category or category == "OTHER":
        category = infer_action_category(event_type, semantic)
    return HumanInteractionEvent(
        participant_id=str(raw["participant_id"]),
        human_run_id=str(raw["human_run_id"]),
        task_id=str(raw["task_id"]),
        event_id=str(raw.get("event_id", "evt-unknown")),
        timestamp_ms=int(raw.get("timestamp_ms", 0)),
        event_type=event_type,
        semantic_target=semantic,
        action_category=category,
        page_state=str(raw.get("page_state", "")),
        outcome=str(raw.get("outcome", "")),
        progress_marker=str(raw.get("progress_marker", "")),
        error_marker=str(raw.get("error_marker", "")),
        metadata=meta,
    )


def normalize_events(raw_events: list[dict[str, Any]]) -> list[HumanInteractionEvent]:
    return [normalize_human_event(e) for e in raw_events]


def action_sequence(events: list[HumanInteractionEvent]) -> list[str]:
    return [e.action_category for e in sorted(events, key=lambda x: x.timestamp_ms)]
