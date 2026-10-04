"""DOM_FAST perception — P2-compatible baseline."""

from __future__ import annotations

import time

from nexo_qa.browser.models import BrowserSnapshot
from nexo_qa.perception.config import PerceptionConfig
from nexo_qa.perception.models import PerceptualScene, WebPercept


class DomFastPerception:
    def __init__(self, config: PerceptionConfig) -> None:
        self.config = config

    def build_scene(self, snapshot: BrowserSnapshot, *, scene_index: int = 0) -> PerceptualScene:
        percepts: list[WebPercept] = []
        vw, vh = snapshot.viewport
        for idx, element in enumerate(snapshot.visible_elements[: self.config.max_percepts], start=1):
            box = element.bounding_box or (0.0, 0.0, 0.0, 0.0)
            x, y, w, h = box
            label = (element.visible_text or element.semantic_hint or element.role or element.tag)[: self.config.max_text_chars_per_percept]
            percepts.append(
                WebPercept(
                    percept_id=f"percept:dom:{scene_index:04d}:{idx:04d}",
                    source_element_id=element.element_id,
                    kind="interactive" if element.tag in ("button", "a", "input") else "content",
                    role=element.role or element.tag,
                    label=label,
                    text=label,
                    semantic_group="main",
                    bounding_box=box,
                    bbox_norm=(x / max(vw, 1), y / max(vh, 1), w / max(vw, 1), h / max(vh, 1)),
                    visual_region="center",
                    viewport_relation="FULLY_VISIBLE",
                    visibility_score=float(element.visibility),
                    salience_score=min(1.0, 0.35 + element.visibility * 0.5),
                    contrast_score=0.5,
                    visual_clutter_score=0.0,
                    attention_cost=0.1,
                    interactive=element.tag in ("button", "a", "input", "textarea") or element.role in ("button", "link"),
                    enabled=element.enabled,
                    state={"editable": element.editable, "checked": element.checked},
                    confidence=1.0,
                    label_source="visible_text",
                    percept_sources=("VISIBLE_TEXT", "ROLE"),
                    is_focused=snapshot.focused_element == element.element_id,
                )
            )
        return PerceptualScene(
            scene_id=f"scene:dom:{scene_index:04d}",
            url=snapshot.url,
            viewport=snapshot.viewport,
            scroll_position=snapshot.scroll_position,
            percepts=tuple(percepts),
            regions=(),
            focused_percept_id=next((p.percept_id for p in percepts if p.is_focused), None),
            attended_percept_ids=tuple(p.percept_id for p in percepts),
            focal_percept_ids=(),
            peripheral_percept_ids=(),
            global_context={"title": snapshot.title, "mode": "dom_fast"},
            timestamp=snapshot.timestamp or time.time(),
            mode="dom_fast",
        )
