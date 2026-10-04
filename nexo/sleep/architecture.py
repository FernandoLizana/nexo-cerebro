"""Máquina de fases de sueño simplificada."""

from __future__ import annotations

from dataclasses import dataclass, field

SLEEP_PHASES: tuple[str, ...] = ("awake", "nrem_light", "nrem_deep", "rem")
_CYCLE = ("nrem_light", "nrem_deep", "nrem_deep", "rem")


@dataclass
class SleepArchitecture:
    """Ciclos NREM/REM derivados de presión de sueño y reloj."""

    phase: str = "awake"
    cycles_completed: int = 0
    total_replays: int = 0
    total_consolidated: int = 0
    sleep_onset_threshold: float = 0.38
    _last_cycle_index: int = field(default=-1, repr=False)

    def update(self, *, sleep_pressure: float, alertness: float, tick: int, fatigue: float = 0.0) -> str:
        effective = sleep_pressure + fatigue * 0.45
        if effective < self.sleep_onset_threshold or alertness > 0.78:
            if self.phase != "awake":
                self.cycles_completed += 1
            self.phase = "awake"
            return self.phase

        cycle_index = (tick // 8) % len(_CYCLE)
        if cycle_index == 0 and self._last_cycle_index == len(_CYCLE) - 1:
            self.cycles_completed += 1
        self._last_cycle_index = cycle_index
        self.phase = _CYCLE[cycle_index]
        return self.phase

    @property
    def is_sleeping(self) -> bool:
        return self.phase != "awake"

    @property
    def allows_replay(self) -> bool:
        return self.phase in ("nrem_light", "nrem_deep", "rem")

    @property
    def allows_consolidation(self) -> bool:
        return self.phase == "nrem_deep"

    def to_dict(self) -> dict[str, int | str]:
        return {
            "phase": self.phase,
            "cycles_completed": self.cycles_completed,
            "total_replays": self.total_replays,
            "total_consolidated": self.total_consolidated,
        }
