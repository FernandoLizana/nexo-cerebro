"""Reloj de simulación — sin dependencia de tiempo de pared."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SimulationClock:
    """Tiempo simulado en ticks discretos."""

    tick: int = 0
    simulation_seconds: float = 0.0
    seconds_per_tick: float = 0.1
    age_ticks: int = 0

    def advance(self, ticks: int = 1) -> None:
        ticks = max(1, int(ticks))
        self.tick += ticks
        self.age_ticks += ticks
        self.simulation_seconds += ticks * self.seconds_per_tick

    @property
    def simulation_time(self) -> float:
        return self.simulation_seconds

    @property
    def circadian_phase(self) -> float:
        """Fase circadiana aproximada [0, 1) en ciclo de 24h simuladas."""
        day_seconds = 86400.0
        return (self.simulation_seconds % day_seconds) / day_seconds

    def to_dict(self) -> dict[str, float | int]:
        return {
            "tick": self.tick,
            "simulation_seconds": self.simulation_seconds,
            "seconds_per_tick": self.seconds_per_tick,
            "circadian_phase": self.circadian_phase,
        }

    @classmethod
    def from_legacy(cls, legacy: object) -> SimulationClock:
        """Adapta nexo.simulation_clock.SimulationClock legacy."""
        tick = int(getattr(legacy, "tick", 0))
        sim = float(getattr(legacy, "sim_time", getattr(legacy, "simulation_seconds", 0.0)))
        dt = float(getattr(legacy, "tick_duration", getattr(legacy, "seconds_per_tick", 0.1)))
        return cls(tick=tick, simulation_seconds=sim, seconds_per_tick=dt, age_ticks=tick)
