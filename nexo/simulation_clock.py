"""Reloj de simulación inyectable (separado del tiempo de pared)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SimulationClock:
    """Tiempo simulado en ticks; no usar datetime.now() en lógica cognitiva."""

    tick: int = 0
    sim_time: float = 0.0
    tick_duration: float = 1.0

    def now(self) -> float:
        return self.sim_time

    def advance(self, delta: float | None = None) -> None:
        dt = self.tick_duration if delta is None else float(delta)
        self.tick += 1
        self.sim_time += dt

    def to_dict(self) -> dict[str, float | int]:
        return {"tick": self.tick, "sim_time": self.sim_time}
