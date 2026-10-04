"""Salience, visibility, geometry helpers — deterministic heuristics."""

from __future__ import annotations

import math

from nexo_qa.perception.config import PerceptionConfig, SalienceWeights


def luminance(r: float, g: float, b: float) -> float:
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: tuple[float, float, float], bg: tuple[float, float, float]) -> float:
    l1 = luminance(*fg) + 0.05
    l2 = luminance(*bg) + 0.05
    return max(l1, l2) / min(l1, l2)


def visual_region(cx: float, cy: float, vw: float, vh: float) -> str:
    vert = "top" if cy < vh * 0.33 else "bottom" if cy > vh * 0.66 else "center"
    horiz = "left" if cx < vw * 0.33 else "right" if cx > vw * 0.66 else "center"
    if vert == "center" and horiz == "center":
        return "center"
    return f"{vert}-{horiz}"


def viewport_relation(
    box: tuple[float, float, float, float],
    viewport: tuple[int, int],
    scroll_y: float,
    occlusion: float,
) -> tuple[str, float]:
    x, y, w, h = box
    vw, vh = viewport
    top = y - scroll_y
    bottom = top + h
    left, right = x, x + w
    if occlusion >= 0.55:
        return "OCCLUDED", 0.0
    if bottom <= 0:
        return "OFFSCREEN_ABOVE", 0.0
    if top >= vh:
        return "OFFSCREEN_BELOW", 0.0
    if right <= 0:
        return "OFFSCREEN_LEFT", 0.0
    if left >= vw:
        return "OFFSCREEN_RIGHT", 0.0
    visible_h = max(0.0, min(bottom, vh) - max(top, 0.0))
    visible_w = max(0.0, min(right, vw) - max(left, 0.0))
    visible_area = visible_w * visible_h
    total_area = max(1.0, w * h)
    vis = min(1.0, visible_area / total_area)
    if vis >= 0.95:
        return "FULLY_VISIBLE", vis
    if vis > 0.05:
        return "PARTIALLY_VISIBLE", vis
    return "UNKNOWN", vis


def compute_salience(
    *,
    area_norm: float,
    centrality: float,
    contrast: float,
    role: str,
    is_focused: bool,
    is_modal: bool,
    weights: SalienceWeights,
) -> float:
    role_prior = {
        "alert": 0.9,
        "button": 0.55,
        "link": 0.45,
        "heading": 0.4,
        "input": 0.35,
        "textbox": 0.35,
    }.get(role, 0.25)
    score = (
        weights.size_weight * area_norm
        + weights.centrality_weight * centrality
        + weights.contrast_weight * min(1.0, contrast / 7.0)
        + weights.role_weight * role_prior
        + (weights.focus_weight if is_focused else 0.0)
        + (weights.modal_weight if is_modal else 0.0)
    )
    return float(max(0.0, min(1.0, score)))


def local_clutter(nearby_count: int, text_density: float) -> float:
    return float(min(1.0, 0.15 * nearby_count + 0.1 * text_density))


def redact_sensitive(text: str, input_type: str) -> str:
    if input_type == "password":
        return "[REDACTED]"
    lowered = text.lower()
    if any(token in lowered for token in ("secret", "token", "api_key")):
        return "[REDACTED]"
    return text
