"""Controlador homeostático — sincroniza cuerpo y estado cognitivo."""

from __future__ import annotations

from dataclasses import dataclass, field

from nexo.body.body_state import VirtualBody
from nexo.body.circadian import CircadianClock
from nexo.body.metabolism import MetabolismEngine
from nexo.core.events import CognitiveEvent


@dataclass
class HomeostaticController:
    body: VirtualBody
    metabolism: MetabolismEngine = field(default_factory=MetabolismEngine)

    def basal_events(self, *, tick: int, simulation_time: float, source: str) -> list[CognitiveEvent]:
        circ = CircadianClock.from_simulation_seconds(simulation_time)
        self.metabolism.circadian_fatigue_multiplier = circ.metabolism_multiplier()
        deltas = self.metabolism.tick_basal(self.body)
        self.body.sleep_pressure = min(1.0, self.body.sleep_pressure + circ.sleep_pressure_bias())
        events: list[CognitiveEvent] = []
        for key, delta in deltas.items():
            if abs(delta) < 1e-9:
                continue
            events.append(
                CognitiveEvent(
                    event_type=f"homeostatic.{key}_changed",
                    source=source,
                    tick=tick,
                    simulation_time=simulation_time,
                    payload={"delta": float(delta)},
                )
            )
        return events

    def sync_from_state(self, homeostatic_dict: dict[str, float]) -> None:
        for k, v in homeostatic_dict.items():
            if hasattr(self.body, k):
                setattr(self.body, k, float(v))
