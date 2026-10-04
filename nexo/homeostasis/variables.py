"""Variables homeostáticas con set point y rangos."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HomeostaticVariable:
    name: str
    value: float
    setpoint: float
    safe_min: float
    safe_max: float
    critical_min: float
    critical_max: float
    priority: float = 1.0

    @property
    def deviation(self) -> float:
        return self.setpoint - self.value

    @property
    def urgency(self) -> float:
        if self.value <= self.critical_min or self.value >= self.critical_max:
            return 2.0 * self.priority
        if self.value < self.safe_min or self.value > self.safe_max:
            return 1.2 * self.priority
        return 0.5 * self.priority

    @property
    def in_safe_range(self) -> bool:
        return self.safe_min <= self.value <= self.safe_max
