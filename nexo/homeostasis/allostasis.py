"""Alostasis — anticipación de necesidades futuras."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.body.body_state import VirtualBody
from nexo.core.events import CognitiveEvent


@dataclass
class AllostaticController:
    """Ajusta metas/goals anticipatoriamente según tendencias corporales."""

    energy_trend_window: int = 5
    _energy_history: list[float] | None = None

    def __post_init__(self) -> None:
        if self._energy_history is None:
            self._energy_history = []

    def update(self, body: VirtualBody) -> None:
        self._energy_history.append(body.energy)
        if len(self._energy_history) > self.energy_trend_window:
            self._energy_history.pop(0)

    @property
    def expected_energy_deficit(self) -> float:
        if len(self._energy_history) < 2:
            return 0.0
        return max(0.0, self._energy_history[0] - self._energy_history[-1])

    def goal_events(
        self, body: VirtualBody, *, tick: int, simulation_time: float, source: str
    ) -> list[CognitiveEvent]:
        self.update(body)
        goals = ["survive"]
        if body.energy < 0.45 or self.expected_energy_deficit > 0.05:
            goals.append("eat")
        if body.sleep_pressure > 0.5 or body.fatigue > 0.6:
            goals.append("rest")
        if body.social_need > 0.5:
            goals.append("social")
        if body.safety_need > 0.45:
            goals.append("avoid_harm")
        return [
            CognitiveEvent(
                event_type="goals.updated",
                source=source,
                tick=tick,
                simulation_time=simulation_time,
                payload={"goals": goals},
            )
        ]
