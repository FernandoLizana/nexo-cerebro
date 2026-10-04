"""
Camino del héroe: etapas, pruebas y dificultades que fuerzan crecimiento.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


STAGES: tuple[dict[str, Any], ...] = (
    {"id": 0, "key": "ordinary_world", "name": "Mundo ordinario", "desc": "La casa conocida."},
    {"id": 1, "key": "call", "name": "Llamada", "desc": "Algo pide salir del confort."},
    {"id": 2, "key": "refusal", "name": "Rechazo", "desc": "Miedo al cambio."},
    {"id": 3, "key": "mentor", "name": "Mentor", "desc": "Un aliado ilumina el camino."},
    {"id": 4, "key": "threshold", "name": "Umbral", "desc": "Cruzar al territorio desconocido."},
    {"id": 5, "key": "ordeal", "name": "Prueba", "desc": "Carencia, frío o hambre forzados."},
    {"id": 6, "key": "reward", "name": "Recompensa", "desc": "Integrar lo aprendido."},
    {"id": 7, "key": "return", "name": "Regreso", "desc": "Volver transformado al hogar."},
)

ORDEALS: tuple[dict[str, Any], ...] = (
    {
        "key": "hunger_trial",
        "label": "Prueba del hambre",
        "drive_scale": {"seek_food": 1.55, "seek_water": 1.2},
        "body_drain": 1.35,
        "tags": ["journey", "ordeal", "hunger"],
    },
    {
        "key": "cold_night",
        "label": "Noche fría en el jardín",
        "drive_scale": {"seek_warmth": 1.6, "seek_rest": 1.25},
        "body_drain": 1.25,
        "tags": ["journey", "ordeal", "cold"],
    },
    {
        "key": "lonely_crossing",
        "label": "Cruce solitario",
        "drive_scale": {"seek_stimulus": 1.4, "seek_rest": 1.15},
        "body_drain": 1.2,
        "tags": ["journey", "ordeal", "solitude"],
    },
    {
        "key": "tower_fall",
        "label": "Torre caída — crisis",
        "drive_scale": {"seek_bathroom": 1.3, "seek_hygiene": 1.35},
        "body_drain": 1.5,
        "valence": -0.45,
        "tags": ["journey", "ordeal", "crisis", "symbol:inflation"],
    },
)


@dataclass
class HeroJourney:
    stage_index: int = 0
    trials_completed: int = 0
    active_ordeal: dict | None = None
    ordeal_ticks_left: int = 0
    rooms_visited: set[str] = field(default_factory=set)
    difficulty: float = 1.0
    completed_cycles: int = 0

    @property
    def stage(self) -> dict:
        return STAGES[min(self.stage_index, len(STAGES) - 1)]

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_index": self.stage_index,
            "stage": self.stage,
            "trials_completed": self.trials_completed,
            "active_ordeal": self.active_ordeal,
            "ordeal_ticks_left": self.ordeal_ticks_left,
            "rooms_visited": sorted(self.rooms_visited),
            "difficulty": round(self.difficulty, 2),
            "completed_cycles": self.completed_cycles,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> HeroJourney:
        if not data:
            return cls()
        hj = cls()
        hj.stage_index = int(data.get("stage_index", 0))
        hj.trials_completed = int(data.get("trials_completed", 0))
        hj.active_ordeal = data.get("active_ordeal")
        hj.ordeal_ticks_left = int(data.get("ordeal_ticks_left", 0))
        hj.rooms_visited = set(data.get("rooms_visited") or [])
        hj.difficulty = float(data.get("difficulty", 1.0))
        hj.completed_cycles = int(data.get("completed_cycles", 0))
        return hj

    def in_ordeal(self) -> bool:
        return self.active_ordeal is not None and self.ordeal_ticks_left > 0

    def drive_multipliers(self) -> dict[str, float]:
        if not self.in_ordeal() or not self.active_ordeal:
            return {}
        return dict(self.active_ordeal.get("drive_scale", {}))

    def body_drain_multiplier(self) -> float:
        if not self.in_ordeal() or not self.active_ordeal:
            return 1.0
        return float(self.active_ordeal.get("body_drain", 1.0)) * self.difficulty

    def on_room(self, room: str) -> None:
        if room:
            self.rooms_visited.add(room)

    def on_hero_zone(self, zone_key: str) -> None:
        if zone_key:
            self.rooms_visited.add(f"zone:{zone_key}")

    def tick(
        self,
        *,
        tick_n: int,
        room: str,
        comfort: float,
        bond: float,
        alive: bool,
        hero_zone: str = "",
        is_night: bool = False,
        light_level: float = 1.0,
    ) -> dict | None:
        if not alive:
            return None

        self.on_room(room)
        if hero_zone:
            self.on_hero_zone(hero_zone)

        if self.in_ordeal():
            self.ordeal_ticks_left -= 1
            if self.ordeal_ticks_left <= 0:
                self.active_ordeal = None
                self.trials_completed += 1
                self._advance_stage()
                return {
                    "type": "journey_ordeal_complete",
                    "stage": self.stage["key"],
                    "trials": self.trials_completed,
                }
            return {
                "type": "journey_ordeal",
                "ordeal": self.active_ordeal,
                "ticks_left": self.ordeal_ticks_left,
            }

        if tick_n % 35 != 0:
            return None

        key = self.stage["key"]
        if key == "call" and (comfort > 0.5 or hero_zone == "call"):
            self._advance_stage()
            return {"type": "journey_stage", "stage": self.stage["key"], "label": self.stage["name"]}
        if key == "refusal" and comfort < 0.42:
            self._advance_stage()
            return {"type": "journey_stage", "stage": self.stage["key"]}
        if key == "mentor" and (bond > 0.55 or hero_zone == "mentor"):
            self._advance_stage()
            return {"type": "journey_stage", "stage": self.stage["key"]}
        if key == "threshold" and (len(self.rooms_visited) >= 4 or hero_zone == "threshold"):
            self._advance_stage()
            return {"type": "journey_stage", "stage": self.stage["key"]}
        if key == "ordeal":
            idx = self.trials_completed % len(ORDEALS)
            if is_night and hero_zone == "threshold":
                idx = 1  # cold_night
            ordeal = dict(ORDEALS[idx])
            self.active_ordeal = ordeal
            self.ordeal_ticks_left = max(8, int(12 * self.difficulty))
            if is_night and light_level < 0.35:
                ordeal["label"] = ordeal.get("label", "prueba") + " (noche)"
            return {"type": "journey_ordeal_start", "ordeal": ordeal}
        if key == "reward":
            self._advance_stage()
            return {"type": "journey_reward", "stage": self.stage["key"]}
        if key == "return":
            self.completed_cycles += 1
            self.difficulty = min(2.2, self.difficulty + 0.12)
            self.stage_index = 0
            self.rooms_visited.clear()
            return {"type": "journey_cycle_complete", "cycles": self.completed_cycles}

        return {"type": "journey_pulse", "stage": key, "comfort": round(comfort, 2)}

    def _advance_stage(self) -> None:
        if self.stage_index < len(STAGES) - 1:
            self.stage_index += 1
