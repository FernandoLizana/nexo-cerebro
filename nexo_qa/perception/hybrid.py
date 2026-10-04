"""HYBRID perception — geometry, visibility, salience, occlusion."""

from __future__ import annotations

import time

from nexo_qa.browser.models import BrowserSnapshot
from nexo_qa.perception.config import PerceptionConfig
from nexo_qa.perception.models import PerceptualRegion, PerceptualScene, WebPercept
from nexo_qa.perception.salience import (
    compute_salience,
    contrast_ratio,
    local_clutter,
    redact_sensitive,
    visual_region,
    viewport_relation,
)


class HybridPerception:
    def __init__(self, config: PerceptionConfig) -> None:
        self.config = config

    def build_scene(self, snapshot: BrowserSnapshot, *, scene_index: int = 0) -> PerceptualScene:
        vw, vh = snapshot.viewport
        scroll = snapshot.scroll_position
        scroll_y = float(scroll[1]) if scroll else 0.0
        raw_meta = snapshot.element_meta or {}
        percepts: list[WebPercept] = []
        centers: list[tuple[float, float]] = []

        for idx, element in enumerate(snapshot.visible_elements[: self.config.max_percepts], start=1):
            meta = dict(raw_meta.get(element.element_id, {}))
            box = element.bounding_box or (0.0, 0.0, 0.0, 0.0)
            x, y, w, h = box
            cx, cy = x + w / 2, y + h / 2
            centers.append((cx, cy))
            occlusion = float(meta.get("occlusion", 0.0))
            rel, vis = viewport_relation(box, snapshot.viewport, 0.0, occlusion)
            if rel.startswith("OFFSCREEN"):
                continue
            if vis <= 0.05 and self.config.compute_occlusion:
                continue
            fg = tuple(meta.get("fg", [0.1, 0.1, 0.1])[:3])
            bg = tuple(meta.get("bg", [1.0, 1.0, 1.0])[:3])
            contrast = contrast_ratio(fg, bg) if self.config.compute_salience else 1.0
            area_norm = min(1.0, (w * h) / max(1.0, vw * vh))
            centrality = 1.0 - min(1.0, ((cx - vw / 2) ** 2 + (cy - vh / 2) ** 2) ** 0.5 / max(vw, vh))
            role = element.role or element.tag
            is_modal = bool(meta.get("isModal", False))
            is_focused = snapshot.focused_element == element.element_id
            sal = compute_salience(
                area_norm=area_norm,
                centrality=centrality,
                contrast=contrast,
                role=role,
                is_focused=is_focused,
                is_modal=is_modal,
                weights=self.config.salience,
            ) if self.config.compute_salience else 0.5
            label = (element.visible_text or element.semantic_hint or role)[: self.config.max_text_chars_per_percept]
            label = redact_sensitive(label, element.input_type)
            text = redact_sensitive(element.visible_text[: self.config.max_text_chars_per_percept], element.input_type)
            label_source = str(meta.get("labelSource", "visible_text"))
            percepts.append(
                WebPercept(
                    percept_id=f"percept:hyb:{scene_index:04d}:{idx:04d}",
                    source_element_id=element.element_id,
                    kind="interactive" if role in ("button", "link", "textbox", "input") else "content",
                    role=role,
                    label=label,
                    text=text,
                    semantic_group=str(meta.get("landmark", "main")),
                    bounding_box=box,
                    bbox_norm=(x / max(vw, 1), y / max(vh, 1), w / max(vw, 1), h / max(vh, 1)),
                    visual_region=visual_region(cx, cy, vw, vh),
                    viewport_relation=rel,  # type: ignore[arg-type]
                    visibility_score=vis,
                    salience_score=sal,
                    contrast_score=min(1.0, contrast / 7.0),
                    visual_clutter_score=0.0,
                    attention_cost=0.08 + (1.0 - vis) * 0.1,
                    interactive=element.tag in ("button", "a", "input", "textarea") or role in ("button", "link", "textbox"),
                    enabled=element.enabled,
                    state={"editable": element.editable, "checked": element.checked, "disabled": not element.enabled},
                    confidence=0.9 if label_source == "visible_text" else 0.7,
                    label_source=label_source,
                    percept_sources=tuple(meta.get("sources", ["VISIBLE_GEOMETRY"])),
                    occlusion_score=occlusion,
                    is_modal=is_modal,
                    is_focused=is_focused,
                )
            )

        if self.config.compute_clutter and percepts:
            enriched: list[WebPercept] = []
            for i, percept in enumerate(percepts):
                cx, cy = centers[i] if i < len(centers) else (0.0, 0.0)
                nearby = sum(1 for j, (ox, oy) in enumerate(centers) if i != j and abs(ox - cx) < 120 and abs(oy - cy) < 80)
                clutter = local_clutter(nearby, min(1.0, len(percept.text) / 40.0))
                enriched.append(replace_percept_clutter(percept, clutter))
            percepts = enriched

        regions = _group_regions(percepts)
        return PerceptualScene(
            scene_id=f"scene:hyb:{scene_index:04d}",
            url=snapshot.url,
            viewport=snapshot.viewport,
            scroll_position=scroll,
            percepts=tuple(percepts),
            regions=regions,
            focused_percept_id=next((p.percept_id for p in percepts if p.is_focused), None),
            attended_percept_ids=(),
            focal_percept_ids=(),
            peripheral_percept_ids=(),
            global_context={
                "title": snapshot.title,
                "mode": "hybrid",
                "scroll_y": scroll_y,
                "percept_count": len(percepts),
            },
            timestamp=snapshot.timestamp or time.time(),
            mode="hybrid",
        )


def replace_percept_clutter(percept: WebPercept, clutter: float) -> WebPercept:
    from dataclasses import replace

    return replace(percept, visual_clutter_score=clutter)


def _group_regions(percepts: list[WebPercept]) -> tuple[PerceptualRegion, ...]:
    groups: dict[str, list[WebPercept]] = {}
    for p in percepts:
        groups.setdefault(p.semantic_group, []).append(p)
    regions: list[PerceptualRegion] = []
    for idx, (name, items) in enumerate(groups.items(), start=1):
        xs = [p.bounding_box[0] for p in items]
        ys = [p.bounding_box[1] for p in items]
        ws = [p.bounding_box[2] for p in items]
        hs = [p.bounding_box[3] for p in items]
        bounds = (min(xs), min(ys), max(x + w for x, w in zip(xs, ws)) - min(xs), max(y + h for y, h in zip(ys, hs)) - min(ys))
        regions.append(
            PerceptualRegion(
                region_id=f"region:{idx:02d}",
                role=name,
                label=name,
                bounds=bounds,
                percept_ids=tuple(p.percept_id for p in items),
                salience=max(p.salience_score for p in items),
            )
        )
    return tuple(regions)
