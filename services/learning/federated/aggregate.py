"""Toy FedAvg + LoRA-delta aggregation (research sandbox only)."""

from __future__ import annotations

from typing import Iterable, Mapping

from services.learning.federated.updates import ClientUpdate


def fedavg(updates: Iterable[ClientUpdate]) -> dict[str, float]:
    """Unweighted mean of client weight dicts (keys union)."""
    items = list(updates)
    if not items:
        return {}
    keys: set[str] = set()
    for u in items:
        keys.update(u.weights)
    out: dict[str, float] = {}
    n = float(len(items))
    for key in keys:
        out[key] = sum(float(u.weights.get(key, 0.0)) for u in items) / n
    return out


def aggregate_lora_deltas(updates: Iterable[ClientUpdate]) -> dict[str, float]:
    items = list(updates)
    if not items:
        return {}
    keys: set[str] = set()
    for u in items:
        keys.update(u.lora_delta)
    n = float(len(items))
    return {k: sum(float(u.lora_delta.get(k, 0.0)) for u in items) / n for k in keys}


def apply_lora(base: Mapping[str, float], delta: Mapping[str, float], *, scale: float = 1.0) -> dict[str, float]:
    merged = {str(k): float(v) for k, v in base.items()}
    for key, value in delta.items():
        merged[key] = float(merged.get(key, 0.0) + scale * float(value))
        merged[key] = max(-1.0, min(1.0, merged[key]))
    return merged
