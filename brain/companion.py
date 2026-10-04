"""
Compañera con cuerpo, persona y química de vínculo con Nexo.
Autonomía desde impulsos internos + atracción par a par (oxitocina).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

from .body import BodyState
from .character import Persona

if TYPE_CHECKING:
    from .chemistry import PeerBond


@dataclass
class CompanionAgent:
    name: str = "Nira"
    species_label: str = "homínido en desarrollo"
    x: float = 280.0
    y: float = 230.0
    agent_dir: int = -1
    gait_phase: float = 0.0
    is_walking: bool = False
    walk_speed: float = 9.0
    body: BodyState = field(default_factory=BodyState)
    persona: Persona = field(default_factory=lambda: Persona(name="Nira"))
    bond_with_nexo: float = 0.42
    _rng: np.random.Generator = field(default_factory=lambda: np.random.default_rng(19))

    def __post_init__(self) -> None:
        self.persona.name = self.name
        self.persona.species_label = self.species_label
        if self.persona.message.startswith("Hola… aún"):
            self.persona.message = "…"

    def apply_care(
        self,
        *,
        bath: bool = False,
        feed: bool = False,
        bathroom: bool = False,
        drink: bool = False,
    ) -> dict:
        applied: list[str] = []
        if bath:
            self.body.bathe(0.6)
            applied.append("baño")
        if bathroom:
            self.body.relieve(0.65)
            applied.append("baño")
        if feed:
            self.body.eat(0.5)
            applied.append("comida")
        if drink:
            self.body.drink(0.4)
            applied.append("agua")
        return {"name": self.name, "applied": applied, "body": self.body.to_dict()}

    def tick(
        self,
        world,
        *,
        room_temp: float,
        sleep_pressure: float = 0.0,
        nexo_x: float,
        nexo_y: float,
        chemistry: PeerBond | None = None,
    ) -> list[dict]:
        """Un paso autónomo: cuerpo + movimiento por impulsos y química."""
        self.body.tick(
            room_temp=room_temp,
            activity=0.12,
            sleep_pressure=sleep_pressure,
            watching_tv=False,
        )
        events: list[dict] = []
        drives = self.body.drives()
        dist = float(np.hypot(nexo_x - self.x, nexo_y - self.y))

        if chemistry:
            chemistry.update_proximity(dist)
            self.bond_with_nexo = chemistry.attraction
            seek_nexo = chemistry.seek_companion_drive()
            if seek_nexo > 0.28 and dist > 35:
                moved = self._step_toward_coords(nexo_x, nexo_y, max_steps=2)
                if moved:
                    events.append({"type": "companion_seek", "name": self.name, "drive": round(seek_nexo, 2)})

        goal = self._drive_goal(world, drives, chemistry=chemistry, nexo_xy=(nexo_x, nexo_y))
        if goal:
            tx, ty = goal
            moved = self._step_toward(world, tx, ty, max_steps=2)
            if moved:
                events.append({"type": "companion_move", "name": self.name})

        if dist < 52:
            if chemistry:
                self.bond_with_nexo = chemistry.attraction
                self.persona.attachment = float(
                    np.clip(0.5 * self.persona.attachment + 0.5 * chemistry.attraction, 0, 1)
                )
            p_social = 0.06 + 0.12 * (chemistry.attraction if chemistry else self.bond_with_nexo)
            if self._rng.random() < p_social:
                events.append({"type": "companion_social", "name": self.name, "target": "Nexo", "dist": round(dist, 1)})

        if self._near_furniture(world, "fridge", 42) and (
            drives.get("seek_food", 0) > 0.28 or drives.get("seek_water", 0) > 0.3
        ):
            self.body.eat(0.35)
            self.body.drink(0.25)
            events.append({"type": "companion_eat", "name": self.name})
        if self._near_furniture(world, "bath", 45) and drives.get("seek_hygiene", 0) > 0.25:
            self.body.bathe(0.4)
            events.append({"type": "companion_bathe", "name": self.name})
        if self._near_furniture(world, "toilet", 42) and drives.get("seek_bathroom", 0) > 0.28:
            self.body.relieve(0.45)
            events.append({"type": "companion_bathroom", "name": self.name})

        if chemistry:
            self.persona.mood = chemistry.companion_mood_from_body(self.body.comfort, drives)
        else:
            self.persona.mood = "content" if self.body.comfort > 0.55 else "calm"
        self.persona.energy = self.body.comfort
        return events

    def _drive_goal(
        self,
        world,
        drives: dict,
        *,
        chemistry: PeerBond | None = None,
        nexo_xy: tuple[float, float] | None = None,
    ) -> tuple[float, float] | None:
        if chemistry and chemistry.seek_companion_drive() > 0.45 and nexo_xy and chemistry.proximity < 0.4:
            return nexo_xy
        if drives.get("seek_bathroom", 0) > 0.3:
            c = world.furniture_center("toilet")
            if c:
                return c
        if drives.get("seek_hygiene", 0) > 0.32:
            c = world.furniture_center("bath")
            if c:
                return c
        if drives.get("seek_food", 0) > 0.32 or drives.get("seek_water", 0) > 0.35:
            c = world.furniture_center("fridge")
            if c:
                return c
        if drives.get("seek_rest", 0) > 0.42:
            c = world.furniture_center("bed")
            if c:
                return c
        if self._rng.random() < 0.12:
            c = world.furniture_center("sofa")
            if c:
                return c
        return None

    def _step_toward_coords(self, tx: float, ty: float, *, max_steps: int = 2) -> int:
        moved = 0
        for _ in range(max_steps):
            dx, dy = tx - self.x, ty - self.y
            dist = float(np.hypot(dx, dy))
            if dist < 8:
                self.is_walking = False
                break
            step = min(self.walk_speed, dist)
            nx = self.x + (dx / dist) * step
            ny = self.y + (dy / dist) * step
            self.x, self.y = nx, ny
            self.agent_dir = -1 if dx < 0 else (1 if dx > 0 else self.agent_dir)
            self.gait_phase = (self.gait_phase + 0.42) % 1.0
            self.is_walking = True
            moved += 1
        return moved

    def _step_toward(self, world, tx: float, ty: float, *, max_steps: int = 2) -> int:
        moved = 0
        for _ in range(max_steps):
            dx, dy = tx - self.x, ty - self.y
            dist = float(np.hypot(dx, dy))
            if dist < 8:
                self.is_walking = False
                break
            step = min(self.walk_speed, dist)
            nx = self.x + (dx / dist) * step
            ny = self.y + (dy / dist) * step
            if world._blocked(nx, ny) or world._collision_furniture(nx, ny):
                self.is_walking = False
                break
            self.x, self.y = nx, ny
            self.agent_dir = -1 if dx < 0 else (1 if dx > 0 else self.agent_dir)
            self.gait_phase = (self.gait_phase + 0.42) % 1.0
            self.is_walking = True
            moved += 1
        return moved

    def _near_furniture(self, world, kind: str, dist: float) -> bool:
        fu = world._furniture(kind)
        if not fu:
            return False
        cx, cy = fu.x + fu.w / 2, fu.y + fu.h / 2
        return float(np.hypot(cx - self.x, cy - self.y)) < dist

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "species_label": self.species_label,
            "x": round(self.x, 1),
            "y": round(self.y, 1),
            "dir": self.agent_dir,
            "gait_phase": round(self.gait_phase, 3),
            "walking": self.is_walking,
            "body": self.body.to_dict(),
            "persona": self.persona.to_dict(),
            "bond_with_nexo": round(self.bond_with_nexo, 3),
        }

    @classmethod
    def from_dict(cls, data: dict) -> CompanionAgent:
        c = cls(
            name=data.get("name", "Nira"),
            species_label=data.get("species_label", "homínido en desarrollo"),
            x=float(data.get("x", 280)),
            y=float(data.get("y", 230)),
            agent_dir=int(data.get("dir", -1)),
            bond_with_nexo=float(data.get("bond_with_nexo", 0.42)),
        )
        if data.get("body"):
            c.body.load_dict(data["body"])
        p = data.get("persona", {})
        c.persona.name = p.get("name", c.name)
        c.persona.mood = p.get("mood", "calm")
        c.persona.message = p.get("message", c.persona.message)
        c.persona.energy = float(p.get("energy", 0.7))
        c.persona.attachment = float(p.get("attachment", 0.35))
        return c
