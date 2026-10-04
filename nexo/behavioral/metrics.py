"""Métricas conductuales integradas."""

from __future__ import annotations

import math
from collections import Counter
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nexo.integrated_runtime import IntegratedRuntime


def compute_metrics(runtime: IntegratedRuntime, result: dict[str, Any]) -> dict[str, float]:
    """Métricas primarias observables desde runtime integrado."""
    actions = result.get("actions_taken") or []
    counts = Counter(actions)
    total = max(len(actions), 1)
    entropy = 0.0
    for c in counts.values():
        p = c / total
        if p > 0:
            entropy -= p * math.log(p + 1e-12)

    rewards = [
        float(ev.payload.get("value", 0.0))
        for ev in runtime.state_store.event_log
        if ev.event_type == "reward.received"
    ]

    return {
        "survival_success": 1.0 if result.get("final_energy", 0.0) > 0.12 else 0.0,
        "final_energy": float(result.get("final_energy", 0.0)),
        "action_entropy": float(entropy),
        "eat_ratio": float(counts.get("eat", 0)) / total,
        "distractor_ratio": float(counts.get("inspect_distractor", 0)) / total,
        "rest_ratio": float(counts.get("rest", 0)) / total,
        "flee_ratio": float(counts.get("flee", 0)) / total,
        "explore_ratio": float(counts.get("explore", 0)) / total,
        "shelter_ratio": float(counts.get("seek_shelter", 0)) / total,
        "distance_traveled": float(getattr(runtime.world, "distance_traveled", 0.0)),
        "social_actions": float(counts.get("approach_caregiver", 0)),
        "mean_reward": float(sum(rewards) / len(rewards)) if rewards else 0.0,
        "total_reward": float(sum(rewards)),
        "event_count": float(result.get("event_count", 0)),
    }
