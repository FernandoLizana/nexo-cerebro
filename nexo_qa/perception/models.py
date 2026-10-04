"""Perceptual web models — serializable, no Playwright/DOM secrets in cognition."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ViewportRelation = Literal[
    "FULLY_VISIBLE",
    "PARTIALLY_VISIBLE",
    "OFFSCREEN_ABOVE",
    "OFFSCREEN_BELOW",
    "OFFSCREEN_LEFT",
    "OFFSCREEN_RIGHT",
    "OCCLUDED",
    "UNKNOWN",
]
AttentionTier = Literal["FOCAL", "PERIPHERAL", "UNATTENDED"]
ExclusionReason = Literal[
    "HIDDEN",
    "OFFSCREEN",
    "OCCLUDED",
    "DISABLED",
    "FILTERED_LOW_RELEVANCE",
    "ATTENTION_LIMIT",
    "POLICY",
    "NOT_INTERACTIVE",
]


@dataclass(frozen=True, slots=True)
class WebPercept:
    percept_id: str
    source_element_id: str
    kind: str
    role: str
    label: str
    text: str
    semantic_group: str
    bounding_box: tuple[float, float, float, float]
    bbox_norm: tuple[float, float, float, float]
    visual_region: str
    viewport_relation: ViewportRelation
    visibility_score: float
    salience_score: float
    contrast_score: float
    visual_clutter_score: float
    attention_cost: float
    interactive: bool
    enabled: bool
    state: dict[str, Any]
    confidence: float
    label_source: str
    percept_sources: tuple[str, ...] = ()
    attention_tier: AttentionTier = "UNATTENDED"
    occlusion_score: float = 0.0
    is_modal: bool = False
    is_focused: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "percept_id": self.percept_id,
            "source_element_id": self.source_element_id,
            "kind": self.kind,
            "role": self.role,
            "label": self.label,
            "text": self.text,
            "semantic_group": self.semantic_group,
            "bounding_box": list(self.bounding_box),
            "bbox_norm": list(self.bbox_norm),
            "visual_region": self.visual_region,
            "viewport_relation": self.viewport_relation,
            "visibility_score": self.visibility_score,
            "salience_score": self.salience_score,
            "contrast_score": self.contrast_score,
            "visual_clutter_score": self.visual_clutter_score,
            "attention_cost": self.attention_cost,
            "interactive": self.interactive,
            "enabled": self.enabled,
            "state": dict(self.state),
            "confidence": self.confidence,
            "label_source": self.label_source,
            "percept_sources": list(self.percept_sources),
            "attention_tier": self.attention_tier,
            "occlusion_score": self.occlusion_score,
            "is_modal": self.is_modal,
            "is_focused": self.is_focused,
        }


@dataclass(frozen=True, slots=True)
class PerceptualRegion:
    region_id: str
    role: str
    label: str
    bounds: tuple[float, float, float, float]
    percept_ids: tuple[str, ...]
    salience: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "region_id": self.region_id,
            "role": self.role,
            "label": self.label,
            "bounds": list(self.bounds),
            "percept_ids": list(self.percept_ids),
            "salience": self.salience,
        }


@dataclass(frozen=True, slots=True)
class PerceptualScene:
    scene_id: str
    url: str
    viewport: tuple[int, int]
    scroll_position: tuple[float, float]
    percepts: tuple[WebPercept, ...]
    regions: tuple[PerceptualRegion, ...]
    focused_percept_id: str | None
    attended_percept_ids: tuple[str, ...]
    focal_percept_ids: tuple[str, ...]
    peripheral_percept_ids: tuple[str, ...]
    global_context: dict[str, Any]
    timestamp: float
    mode: str
    exclusion_audit: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "url": self.url,
            "viewport": list(self.viewport),
            "scroll_position": list(self.scroll_position),
            "percepts": [p.to_dict() for p in self.percepts],
            "regions": [r.to_dict() for r in self.regions],
            "focused_percept_id": self.focused_percept_id,
            "attended_percept_ids": list(self.attended_percept_ids),
            "focal_percept_ids": list(self.focal_percept_ids),
            "peripheral_percept_ids": list(self.peripheral_percept_ids),
            "global_context": dict(self.global_context),
            "timestamp": self.timestamp,
            "mode": self.mode,
            "exclusion_audit": list(self.exclusion_audit),
        }


@dataclass(frozen=True, slots=True)
class PerceptualDiff:
    appeared: tuple[str, ...]
    disappeared: tuple[str, ...]
    moved: tuple[str, ...]
    text_changed: tuple[str, ...]
    state_changed: tuple[str, ...]
    salience_changed: tuple[str, ...]
    focus_changed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "appeared": list(self.appeared),
            "disappeared": list(self.disappeared),
            "moved": list(self.moved),
            "text_changed": list(self.text_changed),
            "state_changed": list(self.state_changed),
            "salience_changed": list(self.salience_changed),
            "focus_changed": self.focus_changed,
        }
