"""Gating contextual del tálamo mediodorsal."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ContextGate:
    """Selecciona política cognitiva relevante según metas y estrés."""

    base_gain: float = 0.7

    def compute(
        self,
        *,
        active_goals: tuple[str, ...],
        stress: float,
        sleep_pressure: float,
    ) -> float:
        gain = self.base_gain
        if "survive" in active_goals or "avoid_harm" in active_goals:
            gain += 0.15
        if sleep_pressure > 0.6:
            gain -= 0.2
        gain -= stress * 0.15
        return max(0.25, min(1.0, gain))
