"""Huella conductual compacta para análisis comparativo."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def compute_behavior_fingerprint(
    metrics: dict[str, float],
    result: dict[str, Any],
) -> dict[str, float | str]:
    """Vector observable resumido — no fenomenológico."""
    return {
        "survival_success": float(metrics.get("survival_success", 0.0)),
        "final_energy": round(float(metrics.get("final_energy", 0.0)), 4),
        "action_entropy": round(float(metrics.get("action_entropy", 0.0)), 4),
        "eat_ratio": round(float(metrics.get("eat_ratio", 0.0)), 4),
        "mean_reward": round(float(metrics.get("mean_reward", 0.0)), 4),
        "trajectory_prefix": str(result.get("trajectory_hash", ""))[:16],
    }


def metric_fingerprint_hash(metrics: dict[str, float]) -> str:
    """Hash estable de métricas primarias para comparación rápida."""
    keys = ("survival_success", "final_energy", "action_entropy", "eat_ratio", "mean_reward")
    payload = {k: round(float(metrics.get(k, 0.0)), 6) for k in keys}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()[:16]
