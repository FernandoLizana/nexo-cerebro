"""Suavizado temporal de acciones seleccionadas."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter


@dataclass
class CerebellarCoordinator:
    """Buffer de acciones recientes para corrección motora."""

    buffer_size: int = 6
    min_consensus: int = 2
    history: list[str] = field(default_factory=list)

    def correct(self, action: str, *, confidence: float) -> tuple[str, float]:
        if not action:
            return action, confidence
        self.history.append(action)
        if len(self.history) > self.buffer_size:
            self.history.pop(0)

        counts = Counter(self.history)
        dominant, count = counts.most_common(1)[0]
        if count >= self.min_consensus and dominant != action:
            smoothed_conf = float(min(0.99, confidence * 0.85 + 0.1 * (count / len(self.history))))
            return dominant, smoothed_conf
        return action, confidence

    def reset(self) -> None:
        self.history.clear()
