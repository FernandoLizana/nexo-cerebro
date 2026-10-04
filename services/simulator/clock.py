"""Shared simulation clock (logical time; not wall-clock networking)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SimClock:
    """Monotonic discrete-event clock in abstract time units."""

    now: float = 0.0

    def advance_to(self, t: float) -> None:
        if t < self.now:
            raise ValueError(f"clock cannot go backwards: {t} < {self.now}")
        self.now = float(t)
