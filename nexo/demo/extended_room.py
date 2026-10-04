"""RoomWorld extendido con clima y refugio (Sprint 24)."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.demo.room_scenario import RoomWorld


@dataclass
class ExtendedRoomWorld(RoomWorld):
    """Añade presión climática y acción seek_shelter."""

    weather_level: float = 0.2
    shelter_available: bool = True
    in_shelter: bool = False

    def percepts_for_agent(self) -> list[tuple[str, float, tuple[float, ...]]]:
        percepts = super().percepts_for_agent()
        if self.weather_level > 0.15:
            percepts.append(("weather", self.weather_level, (0.4, 0.6, 0.9)))
        if self.shelter_available and not self.in_shelter:
            percepts.append(("shelter", 0.3 + self.weather_level * 0.4, (0.6, 0.6, 0.7)))
        return percepts

    def available_actions(self) -> tuple[str, ...]:
        actions = list(super().available_actions())
        if self.shelter_available and self.weather_level > 0.25:
            actions.append("seek_shelter")
        return tuple(dict.fromkeys(actions))

    def action_info(self, action: str) -> dict:
        if action == "seek_shelter":
            return {
                "base_value": 0.28 + self.weather_level * 0.2,
                "cost_energy": 0.05,
                "risk": 0.02,
                "modality": "shelter",
            }
        return super().action_info(action)

    def apply_action(self, action: str) -> dict:
        if action == "seek_shelter" and self.shelter_available:
            self.ticks += 1
            self.action_history.append(action)
            self.in_shelter = True
            self.weather_level = max(0.0, self.weather_level - 0.35)
            reward = 0.4 if self.weather_level < 0.4 else 0.2
            return {
                "reward": reward,
                "homeostatic_deltas": {"energy": -0.03, "fatigue": -0.05},
                "encoded_memory": None,
            }
        if action == "explore":
            self.in_shelter = False
        result = super().apply_action(action)
        if self.ticks % 5 == 0 and not self.in_shelter:
            self.weather_level = min(1.0, self.weather_level + 0.08)
        return result
