"""Perception configuration — modes, limits, salience weights."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SalienceWeights:
    """ENGINEERING DEFAULT — NOT HUMAN-CALIBRATED."""

    size_weight: float = 0.25
    centrality_weight: float = 0.15
    contrast_weight: float = 0.15
    role_weight: float = 0.15
    focus_weight: float = 0.2
    modal_weight: float = 0.25
    heading_weight: float = 0.1

    @classmethod
    def from_mapping(cls, data: dict | None) -> SalienceWeights:
        data = data or {}
        return cls(
            size_weight=float(data.get("size_weight", 0.25)),
            centrality_weight=float(data.get("centrality_weight", 0.15)),
            contrast_weight=float(data.get("contrast_weight", 0.15)),
            role_weight=float(data.get("role_weight", 0.15)),
            focus_weight=float(data.get("focus_weight", 0.2)),
            modal_weight=float(data.get("modal_weight", 0.25)),
            heading_weight=float(data.get("heading_weight", 0.1)),
        )


@dataclass
class PerceptionConfig:
    mode: str = "dom_fast"  # dom_fast | hybrid | vision
    max_percepts: int = 24
    max_attended_percepts: int = 8
    max_focal_percepts: int = 4
    max_text_chars_per_percept: int = 120
    max_total_scene_text: int = 2000
    include_geometry: bool = True
    include_accessibility: bool = True
    compute_salience: bool = True
    compute_clutter: bool = True
    compute_occlusion: bool = True
    screenshot_policy: str = "keyframes"  # none | keyframes | all | failure_only
    salience: SalienceWeights = field(default_factory=SalienceWeights)
    occlusion_threshold: float = 0.55
    min_visibility_for_action: float = 0.35

    @classmethod
    def from_mapping(cls, data: dict | None) -> PerceptionConfig:
        data = dict(data or {})
        return cls(
            mode=str(data.get("mode", "dom_fast")),
            max_percepts=int(data.get("max_percepts", 24)),
            max_attended_percepts=int(data.get("max_attended_percepts", 8)),
            max_focal_percepts=int(data.get("max_focal_percepts", 4)),
            max_text_chars_per_percept=int(data.get("max_text_chars_per_percept", 120)),
            max_total_scene_text=int(data.get("max_total_scene_text", 2000)),
            include_geometry=bool(data.get("include_geometry", True)),
            include_accessibility=bool(data.get("include_accessibility", True)),
            compute_salience=bool(data.get("compute_salience", True)),
            compute_clutter=bool(data.get("compute_clutter", True)),
            compute_occlusion=bool(data.get("compute_occlusion", True)),
            screenshot_policy=str(data.get("screenshot_policy", "keyframes")),
            salience=SalienceWeights.from_mapping(data.get("salience")),
            occlusion_threshold=float(data.get("occlusion_threshold", 0.55)),
            min_visibility_for_action=float(data.get("min_visibility_for_action", 0.35)),
        )
