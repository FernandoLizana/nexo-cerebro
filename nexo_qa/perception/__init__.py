"""Perceptual web model for NEXO Cognitive QA (P3)."""

from __future__ import annotations

from nexo_qa.perception.attention_gate import PerceptualAttentionGate
from nexo_qa.perception.config import PerceptionConfig, SalienceWeights
from nexo_qa.perception.diff import diff_scenes
from nexo_qa.perception.models import PerceptualDiff, PerceptualScene, WebPercept
from nexo_qa.perception.strategy import PerceptionStrategy, perception_strategy_for

__all__ = [
    "PerceptionConfig",
    "SalienceWeights",
    "WebPercept",
    "PerceptualScene",
    "PerceptualDiff",
    "PerceptualAttentionGate",
    "PerceptionStrategy",
    "perception_strategy_for",
    "diff_scenes",
]
