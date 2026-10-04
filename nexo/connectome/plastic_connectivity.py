"""Plasticidad sináptica acotada en el conectoma."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PlasticityState:
    weights: dict[tuple[str, str], float] = field(default_factory=dict)
    min_weight: float = 0.01
    max_weight: float = 2.0

    def get_weight(self, source: str, target: str, base: float) -> float:
        key = (source, target)
        return self.weights.get(key, base)

    def update(self, source: str, target: str, delta: float, *, rule: str = "hebbian") -> float:
        key = (source, target)
        old = self.weights.get(key, 1.0)
        new = max(self.min_weight, min(self.max_weight, old + delta))
        self.weights[key] = new
        return new
