"""VISION mode stub — not implemented in P3."""

from __future__ import annotations

from nexo_qa.browser.models import BrowserSnapshot
from nexo_qa.perception.config import PerceptionConfig
from nexo_qa.perception.models import PerceptualScene


class VisionPerceptionStub:
    STATUS = "NOT_IMPLEMENTED"

    def __init__(self, config: PerceptionConfig) -> None:
        self.config = config

    def build_scene(self, snapshot: BrowserSnapshot, *, scene_index: int = 0) -> PerceptualScene:
        raise NotImplementedError("VISION perception mode is not implemented in P3 (use dom_fast or hybrid)")
