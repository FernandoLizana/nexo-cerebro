"""Modulación circadiana sobre metabolismo y alerta."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass
class CircadianClock:
    """Fase circadiana derivada del reloj simulado."""

    phase: float = 0.0  # 0..1

    @classmethod
    def from_simulation_seconds(cls, seconds: float) -> CircadianClock:
        day = 86400.0
        return cls(phase=(seconds % day) / day)

    def alertness(self) -> float:
        """Máxima ~fase 0.25 (mañana simulada), mínima ~0.75 (noche)."""
        return 0.5 + 0.5 * math.cos(2 * math.pi * (self.phase - 0.25))

    def metabolism_multiplier(self) -> float:
        """Metabolismo ligeramente mayor durante "día" simulado."""
        return 0.85 + 0.3 * self.alertness()

    def sleep_pressure_bias(self) -> float:
        return max(0.0, -self.alertness() * 0.0002)
