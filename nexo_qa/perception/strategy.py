"""Perception strategy protocol and factory."""

from __future__ import annotations

from typing import Protocol

from nexo_qa.browser.models import BrowserSnapshot
from nexo_qa.perception.config import PerceptionConfig
from nexo_qa.perception.dom_fast import DomFastPerception
from nexo_qa.perception.hybrid import HybridPerception
from nexo_qa.perception.models import PerceptualScene
from nexo_qa.perception.vision import VisionPerceptionStub


class PerceptionStrategy(Protocol):
    def build_scene(self, snapshot: BrowserSnapshot, *, scene_index: int = 0) -> PerceptualScene:
        ...


def perception_strategy_for(config: PerceptionConfig) -> PerceptionStrategy:
    mode = config.mode.lower()
    if mode == "hybrid":
        return HybridPerception(config)
    if mode == "vision":
        return VisionPerceptionStub(config)
    return DomFastPerception(config)
