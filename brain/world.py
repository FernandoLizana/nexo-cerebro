"""
Hogar 2D de Nexo: jardín, casa, escritorio (libros), TV (YouTube), cocina, cama.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .archetype_cards import (
    TOUCH_EVENT,
    card_key_from_meta,
    is_archetype_card_meta,
    normalize_card_meta,
    object_id_for,
)
from .curiosity import (
    ARCHETYPE_CARD_RETOUCH_THRESHOLD,
    ARCHETYPE_CARD_TOUCH_THRESHOLD,
    BOOK_READ_THRESHOLD,
)
from .environment import WorldClock, ambient_temperature, apply_circadian_drives, hero_zone_for_room


MODALITY_CHANNELS = {
    "world": 0,
    "image": 1,
    "document": 2,
    "audio": 3,
    "text": 4,
    "social": 5,
    "video": 6,
}


@dataclass
class WorldObject:
    id: str
    kind: str
    x: float
    y: float
    label: str = ""
    modality: str = "world"
    memory_key: str = ""
    radius: float = 16.0
    zone: str = "house"
    meta: dict = field(default_factory=dict)


@dataclass
class Furniture:
    id: str
    kind: str
    x: float
    y: float
    w: float
    h: float
    label: str


@dataclass
class World2D:
    width: float = 640.0
    height: float = 400.0
    agent_x: float = 200.0
    agent_y: float = 210.0
    agent_z: float = 0.0
    agent_dir: int = 1
    gait_phase: float = 0.0
    is_walking: bool = False
    walk_speed: float = 9.0
    _walk_goal: tuple[float, float] | None = field(default=None, init=False)
    view_radius: float = 110.0
    objects: list[WorldObject] = field(default_factory=list)
    furniture: list[Furniture] = field(default_factory=list)
    trees: list[dict] = field(default_factory=list)
    pantry: list[dict] = field(default_factory=list)
    tv_state: dict = field(default_factory=dict)
    web_state: dict = field(default_factory=dict)
    clock: WorldClock = field(default_factory=WorldClock)
    # Arena Level 2: si True, beber solo de fuentes novel (no nevera).
    water_only_novel: bool = False
    # Arena Level 2.3: si True, comer solo del cuenco novel (no nevera).
    food_only_novel: bool = False
    # Arena Level 2.4: higiene solo vía bañera novel (sin GPS gratis).
    hygiene_only_novel: bool = False
    # Arena: fuente presente pero sin agua (aprendizaje de fallo).
    fountain_is_dry: bool = False
    # Arena 2.5: object_ids concretos secos (discriminación bueno/malo).
    dry_object_ids: set[str] = field(default_factory=set)
    # Arena: locomoción discreta rápida (reproducible); no altera choice_key.
    arena_fast_locomotion: bool = False
    _attention_target: tuple[float, float] | None = field(default=None, init=False)
    _rng: np.random.Generator = field(default_factory=lambda: np.random.default_rng(7))
    _desk_slots: int = field(default=0, init=False)

    def bind_rng(self, rng: np.random.Generator) -> None:
        """Conecta el generador del flujo world (reproducibilidad)."""
        self._rng = rng

    def __post_init__(self) -> None:
        self.ensure_home()

    def ensure_home(self) -> None:
        """Garantiza mobiliario y árboles (p. ej. tras cargar estado viejo)."""
        if not self.furniture:
            self._build_home()
        else:
            self._ensure_bathroom()
        if not self.trees:
            for i in range(5):
                self.trees.append(
                    {
                        "x": float(30 + i * 28),
                        "y": float(60 + (i % 3) * 45),
                        "r": float(16 + (i % 2) * 6),
                    }
                )
        if not self.tv_state:
            self.tv_state = {"active": False, "query": "", "title": "", "video_id": "", "url": ""}
        if not self.web_state:
            self.web_state = {"active": False, "query": "", "provider": "", "results": []}
        from .food_system import ensure_garden_crops, ensure_stove

        ensure_garden_crops(self)
        ensure_stove(self)

    def _ensure_bathroom(self) -> None:
        kinds = {f.kind for f in self.furniture}
        if "bath" not in kinds:
            self.furniture.append(
                Furniture("bath", "bath", 395, 288, 72, 58, "bañera")
            )
        if "toilet" not in kinds:
            self.furniture.append(
                Furniture("toilet", "toilet", 475, 292, 48, 52, "inodoro")
            )

    def _build_home(self) -> None:
        self.trees.clear()
        for i in range(5):
            self.trees.append(
                {
                    "x": float(30 + i * 28),
                    "y": float(60 + (i % 3) * 45),
                    "r": float(16 + (i % 2) * 6),
                }
            )
        self.furniture = [
            Furniture("door", "door", 178, 175, 8, 70, "puerta"),
            Furniture("desk", "desk", 500, 55, 120, 55, "escritorio"),
            Furniture("tv", "tv", 340, 88, 90, 52, "televisión"),
            Furniture("fridge", "fridge", 230, 290, 55, 70, "nevera"),
            Furniture("bed", "bed", 520, 285, 95, 55, "cama"),
            Furniture("sofa", "sofa", 300, 220, 100, 45, "sofá"),
            Furniture("bath", "bath", 395, 288, 72, 58, "bañera"),
            Furniture("toilet", "toilet", 475, 292, 48, 52, "inodoro"),
        ]
        self.tv_state = {"active": False, "query": "", "title": "", "video_id": "", "url": ""}
        self.web_state = {"active": False, "query": "", "provider": "", "results": []}

    def current_room(self) -> str:
        if self.agent_x < 175:
            return "jardín"
        if self._in_zone("desk"):
            return "escritorio"
        if self._in_zone("tv"):
            return "sala_tv"
        if self._in_zone("fridge"):
            return "cocina"
        if self._in_zone("stove"):
            return "cocina"
        if self._in_zone("bath") or self._in_zone("toilet"):
            return "baño"
        if self._in_zone("bed"):
            return "dormitorio"
        return "casa"

    def room_temperature(self) -> float:
        room = self.current_room()
        if room == "jardín":
            base = 0.38
        elif room == "cocina":
            base = 0.68
        elif room == "baño":
            base = 0.72
        else:
            base = 0.62
        env = self.ambient()
        return ambient_temperature(
            room,
            phase=env["phase"],
            season=env["season"],
            base=base,
            hour=int(env.get("hour", 12)),
        )

    def hero_zone(self) -> dict[str, str]:
        return hero_zone_for_room(self.current_room())

    def hero_zone_key(self) -> str:
        return self.hero_zone()["key"]

    def ambient(self) -> dict:
        phase = self.clock.phase()
        return {
            **self.clock.to_dict(),
            "hero_zone": self.hero_zone(),
        }

    def advance_clock(self, n: int = 1) -> None:
        self.clock.advance(n)
        from .food_system import tick_crops

        for _ in range(max(1, n)):
            tick_crops(self)

    def _in_zone(self, kind: str) -> bool:
        f = self._furniture(kind)
        if not f:
            return False
        return f.x <= self.agent_x <= f.x + f.w and f.y <= self.agent_y <= f.y + f.h

    def _furniture(self, kind: str) -> Furniture | None:
        for fu in self.furniture:
            if fu.kind == kind:
                return fu
        return None

    def add_stimulus_object(
        self,
        *,
        label: str,
        modality: str,
        memory_key: str = "",
        x: float | None = None,
        y: float | None = None,
    ) -> WorldObject:
        if modality in ("document", "text") or kind_from_modality(modality) == "book":
            return self.add_book_to_desk(label=label, modality=modality, memory_key=memory_key)
        obj = WorldObject(
            id=memory_key or f"obj-{len(self.objects)}",
            kind=kind_from_modality(modality),
            x=x if x is not None else float(self._rng.uniform(200, self.width - 40)),
            y=y if y is not None else float(self._rng.uniform(160, self.height - 50)),
            label=label[:80],
            modality=modality,
            memory_key=memory_key,
        )
        self.objects.append(obj)
        return obj

    def add_book_to_desk(
        self,
        *,
        label: str,
        modality: str,
        memory_key: str = "",
        obj_id: str = "",
        meta: dict | None = None,
    ) -> WorldObject:
        desk = self._furniture("desk")
        if not desk:
            return self.add_stimulus_object(label=label, modality=modality, memory_key=memory_key)
        col = self._desk_slots % 4
        row = self._desk_slots // 4
        self._desk_slots += 1
        obj = WorldObject(
            id=obj_id or memory_key or f"book-{len(self.objects)}",
            kind="book",
            x=desk.x + 18 + col * 26,
            y=desk.y + 12 + row * 22,
            label=label[:80],
            modality=modality if modality in ("document", "text") else "document",
            memory_key=memory_key,
            radius=12.0,
            zone="desk",
            meta=dict(meta or {}),
        )
        self.objects.append(obj)
        return obj

    def add_archetype_card(self, *, card_key: str, name_es: str, memory_key: str = "") -> WorldObject:
        key = card_key_from_meta({"archetype_card": card_key}) or card_key
        return self.add_book_to_desk(
            label=f"◈ {name_es}",
            modality="text",
            memory_key=memory_key,
            obj_id=object_id_for(key),
            meta=normalize_card_meta({"archetype_card": key, "kind": "archetype_card"}),
        )

    def furniture_center(self, kind: str) -> tuple[float, float] | None:
        fu = self._furniture(kind)
        if not fu:
            return None
        return fu.x + fu.w / 2, fu.y + fu.h / 2

    def nearest_furniture_center(
        self, kind: str, *, x: float | None = None, y: float | None = None
    ) -> tuple[float, float] | None:
        """Centro del mueble de ``kind`` más cercano al agente (o a x,y)."""
        ax = float(self.agent_x if x is None else x)
        ay = float(self.agent_y if y is None else y)
        best: tuple[float, float] | None = None
        best_d = 1e18
        for fu in self.furniture:
            if fu.kind != kind:
                continue
            cx, cy = fu.x + fu.w / 2, fu.y + fu.h / 2
            d = (cx - ax) ** 2 + (cy - ay) ** 2
            if d < best_d:
                best_d = d
                best = (cx, cy)
        return best

    def furniture_by_id(self, object_id: str) -> Furniture | None:
        oid = str(object_id or "")
        for fu in self.furniture:
            if fu.id == oid:
                return fu
        return None

    def ensure_novel_fountain(
        self,
        *,
        x: float = 72.0,
        y: float = 190.0,
        object_id: str = "novel-fountain",
        label: str = "fuente desconocida",
    ) -> Furniture:
        """Fuente de agua distinta a la nevera (permite varias por object_id)."""
        existing = self.furniture_by_id(object_id)
        if existing:
            return existing
        fu = Furniture(object_id, "fountain", float(x), float(y), 36.0, 36.0, label)
        self.furniture.append(fu)
        return fu

    def ensure_novel_food_bowl(
        self,
        *,
        x: float = 310.0,
        y: float = 240.0,
        object_id: str = "novel-bowl",
        label: str = "cuenco desconocido",
    ) -> Furniture:
        """Cuenco de comida distinto a la nevera (permite varios por object_id)."""
        existing = self.furniture_by_id(object_id)
        if existing:
            return existing
        fu = Furniture(object_id, "food_bowl", float(x), float(y), 32.0, 32.0, label)
        self.furniture.append(fu)
        return fu

    def ensure_novel_bath(
        self,
        *,
        x: float = 280.0,
        y: float = 200.0,
        object_id: str = "novel-bath",
        label: str = "bañera desconocida",
    ) -> Furniture:
        """Bañera novel para Arena higiene Level 2.4."""
        existing = self.furniture_by_id(object_id)
        if existing:
            return existing
        fu = Furniture(object_id, "bath", float(x), float(y), 48.0, 40.0, label)
        self.furniture.append(fu)
        return fu

    def _nearest_furniture(
        self, kind: str, *, max_dist: float = 52.0
    ):
        """Mueble de ``kind`` más cercano dentro de max_dist, o None."""
        best = None
        best_d = max_dist * max_dist
        for fu in self.furniture:
            if fu.kind != kind:
                continue
            cx, cy = fu.x + fu.w / 2, fu.y + fu.h / 2
            d = (cx - self.agent_x) ** 2 + (cy - self.agent_y) ** 2
            if d <= best_d:
                best_d = d
                best = fu
        return best

    def is_object_dry(self, object_id: str) -> bool:
        if self.fountain_is_dry:
            return True
        return str(object_id or "") in self.dry_object_ids

    def remove_furniture_id(self, object_id: str) -> bool:
        oid = str(object_id or "")
        before = len(self.furniture)
        self.furniture = [fu for fu in self.furniture if fu.id != oid]
        return len(self.furniture) < before

    def remove_furniture_kind(self, kind: str) -> int:
        before = len(self.furniture)
        self.furniture = [fu for fu in self.furniture if fu.kind != kind]
        return before - len(self.furniture)

    def point_attention(self, kind: str) -> None:
        c = self.furniture_center(kind)
        if c:
            self._attention_target = c
        else:
            self._attention_target = None

    def step_toward(self, tx: float, ty: float, *, max_steps: int = 5, speed: float = 15.0) -> int:
        moved = 0
        moves = {0: (-speed, 0), 1: (speed, 0), 2: (0, -speed), 3: (0, speed)}
        for _ in range(max_steps):
            dx, dy = tx - self.agent_x, ty - self.agent_y
            if abs(dx) < 14 and abs(dy) < 14:
                break
            if abs(dx) >= abs(dy):
                m = 1 if dx > 0 else 0
            else:
                m = 3 if dy > 0 else 2
            ddx, ddy = moves[m]
            nx, ny = self.agent_x + ddx, self.agent_y + ddy
            if not self._blocked(nx, ny):
                self.agent_x, self.agent_y = nx, ny
                self.agent_dir = -1 if ddx < 0 else (1 if ddx > 0 else self.agent_dir)
                moved += 1
        return moved

    def _collision_furniture(self, x: float, y: float) -> Furniture | None:
        pad = 6.0
        for fu in self.furniture:
            if fu.kind == "door":
                continue
            if (
                fu.x + pad <= x <= fu.x + fu.w - pad
                and fu.y + pad <= y <= fu.y + fu.h - pad
            ):
                return fu
        return None

    def ensure_agent_free(self) -> bool:
        """Evita que el agente quede atrapado dentro de un mueble (estado guardado)."""
        if not self._collision_furniture(self.agent_x, self.agent_y):
            return False
        candidates = [
            (self.agent_x, self.agent_y + 22),
            (self.agent_x, self.agent_y - 22),
            (self.agent_x + 22, self.agent_y),
            (self.agent_x - 22, self.agent_y),
            (240.0, 230.0),
            (320.0, 250.0),
            (220.0, 280.0),
        ]
        for tx, ty in candidates:
            if not self._blocked(tx, ty) and not self._collision_furniture(tx, ty):
                self.agent_x, self.agent_y = tx, ty
                self.is_walking = False
                return True
        self.agent_x, self.agent_y = 240.0, 230.0
        return True

    def _try_step(self, nx: float, ny: float, *, dx: float = 0.0) -> bool:
        if self._blocked(nx, ny) or self._collision_furniture(nx, ny):
            return False
        self.agent_x, self.agent_y = nx, ny
        if dx:
            self.agent_dir = -1 if dx < 0 else 1
        self.gait_phase = (self.gait_phase + 0.42) % 1.0
        self.is_walking = True
        return True

    def _escape_furniture(self, step: float) -> bool:
        hit = self._collision_furniture(self.agent_x, self.agent_y)
        if not hit:
            return False
        cx = hit.x + hit.w / 2
        cy = hit.y + hit.h / 2
        ex = self.agent_x - cx
        ey = self.agent_y - cy
        if abs(ex) < 0.5 and abs(ey) < 0.5:
            ex, ey = 1.0, 0.0
        norm = float(np.hypot(ex, ey)) or 1.0
        for mul in (1.0, 1.35, 1.75, 2.2):
            nx = self.agent_x + (ex / norm) * step * mul
            ny = self.agent_y + (ey / norm) * step * mul
            if self._try_step(nx, ny, dx=ex):
                return True
        return False

    def _blocked(self, x: float, y: float, margin: float = 12.0) -> bool:
        if x < margin or y < margin or x > self.width - margin or y > self.height - margin:
            return True
        if x < 175:
            for t in self.trees:
                if np.hypot(x - t["x"], y - t["y"]) < t["r"] + margin * 0.35:
                    return True
        return False

    def encode_perception(self, n_sensory: int, *, interoception: np.ndarray | None = None) -> np.ndarray:
        vec = np.zeros(n_sensory, dtype=np.float32)
        grid_n = min(48, n_sensory // 8)
        side = int(np.ceil(np.sqrt(grid_n)))
        cell = (2 * self.view_radius) / side

        for gy in range(side):
            for gx in range(side):
                idx = gy * side + gx
                if idx >= grid_n:
                    break
                wx = self.agent_x - self.view_radius + (gx + 0.5) * cell
                wy = self.agent_y - self.view_radius + (gy + 0.5) * cell
                val = 0.0
                if wx >= 175:
                    val = 0.25
                for obj in self.objects:
                    if np.hypot(wx - obj.x, wy - obj.y) < obj.radius:
                        val = max(val, 0.5)
                for fu in self.furniture:
                    if fu.x <= wx <= fu.x + fu.w and fu.y <= wy <= fu.y + fu.h:
                        val = max(val, 0.65 if fu.kind == "tv" else 0.45)
                vec[idx] = float(np.clip(val, 0, 1))

        offset = grid_n
        nearby = sorted(self.objects, key=lambda o: np.hypot(o.x - self.agent_x, o.y - self.agent_y))[:5]
        sector = max(6, (n_sensory - offset - 16) // 6)
        for i, obj in enumerate(nearby):
            d = float(np.hypot(obj.x - self.agent_x, obj.y - self.agent_y))
            if d > self.view_radius * 1.3:
                continue
            base = offset + i * sector
            if base + 3 >= n_sensory:
                break
            vec[base] = float(np.clip(1 - d / (self.view_radius * 1.4), 0, 1))
            vec[base + 1] = MODALITY_CHANNELS.get(obj.modality, 0) / 10.0
            vec[base + 2] = 1.0 if obj.kind == "book" else 0.0

        if self.tv_state.get("active"):
            base = n_sensory - 12
            if base >= 0:
                vec[base] = 0.9
                vec[base + 1] = 0.6
        if self.web_state.get("active"):
            base = n_sensory - 14
            if base >= 0:
                vec[base] = 0.85
                vec[base + 2] = 0.55

        if interoception is not None and interoception.size:
            n_i = min(int(interoception.size), 12, n_sensory - 16)
            vec[n_sensory - 16 : n_sensory - 16 + n_i] = interoception[:n_i]

        m = float(vec.max())
        if m > 1e-6:
            vec /= m
        return vec

    def set_walk_goal(self, x: float, y: float) -> None:
        self._walk_goal = (float(x), float(y))

    def clear_walk_goal(self) -> None:
        self._walk_goal = None
        self.is_walking = False

    def locomote_toward(self, tx: float, ty: float, *, max_step: float | None = None) -> bool:
        """Un paso suave hacia el objetivo — como caminar."""
        step = max_step if max_step is not None else self.walk_speed
        dx, dy = tx - self.agent_x, ty - self.agent_y
        dist = float(np.hypot(dx, dy))
        if dist < 6.0:
            self.is_walking = False
            return False
        move = min(step, dist)
        nx = self.agent_x + (dx / dist) * move
        ny = self.agent_y + (dy / dist) * move
        if self._try_step(nx, ny, dx=dx):
            return True
        if self._try_step(nx, self.agent_y, dx=dx):
            return True
        if self._try_step(self.agent_x, ny, dx=dx):
            return True
        if self._escape_furniture(step):
            return True
        self.is_walking = False
        return False

    def locomote_direction(self, motor: int, *, steps: int = 1) -> int:
        """Pasos discretos en una dirección con interpolación."""
        moves = {0: (-1, 0), 1: (1, 0), 2: (0, -1), 3: (0, 1)}
        if motor not in moves:
            return 0
        ux, uy = moves[motor]
        moved = 0
        for _ in range(steps):
            nx = self.agent_x + ux * self.walk_speed
            ny = self.agent_y + uy * self.walk_speed
            if self._try_step(nx, ny, dx=ux):
                moved += 1
                continue
            if self._escape_furniture(self.walk_speed):
                moved += 1
                continue
            break
        if moved == 0:
            self.is_walking = False
        return moved

    def apply_motor(
        self,
        motor: list[int],
        *,
        drives: dict | None = None,
        biomech=None,
        choice_key: str = "",
        brain=None,
    ) -> dict:
        events: list[dict] = []
        drives = drives or {}

        if biomech is not None and not getattr(self, "arena_fast_locomotion", False):
            return self._apply_motor_physics(
                motor, drives=drives, biomech=biomech, choice_key=choice_key, brain=brain
            )

        if self._walk_goal:
            gx, gy = self._walk_goal
            if self.locomote_toward(gx, gy):
                events.append({"type": "move", "motor": "walk", "gait": round(self.gait_phase, 2)})
            elif float(np.hypot(gx - self.agent_x, gy - self.agent_y)) < 14:
                self.clear_walk_goal()

        for m in motor:
            if m in (0, 1, 2, 3):
                n = self.locomote_direction(m)
                if n:
                    events.append({"type": "move", "motor": m, "gait": round(self.gait_phase, 2)})
                else:
                    region = "limbs"
                    pain = 0.04
                    hit = self._collision_furniture(self.agent_x, self.agent_y)
                    if hit:
                        region = "limbs" if hit.kind != "desk" else "head"
                        pain = 0.06 if hit.kind in ("desk", "fridge") else 0.045
                    events.append({"type": "bump", "region": region, "pain": pain, "target": hit.label if hit else ""})

        if self._attention_target:
            ax, ay = self._attention_target
            if np.hypot(ax - self.agent_x, ay - self.agent_y) < 20:
                self._attention_target = None

        interact = 4 in motor or any(m >= 5 for m in motor)
        if interact:
            ev = self._interact(drives, choice_key=choice_key, brain=brain)
            if ev:
                events.append(ev)

        return {
            "events": events,
            "position": {"x": round(self.agent_x, 1), "y": round(self.agent_y, 1), "dir": self.agent_dir},
            "room": self.current_room(),
        }

    def _apply_motor_physics(
        self,
        motor: list[int],
        *,
        drives: dict | None = None,
        biomech=None,
        choice_key: str = "",
        brain=None,
    ) -> dict:
        events: list[dict] = []
        drives = drives or {}
        walk_goal = self._walk_goal

        dx, dy, meta = biomech.integrate(self, motor, walk_goal=walk_goal)
        speed_before = float(np.hypot(biomech.vx, biomech.vy))

        moved = False
        attempted_move = abs(dx) > 1e-6 or abs(dy) > 1e-6
        if attempted_move:
            nx, ny = self.agent_x + dx, self.agent_y + dy
            if self._try_step(nx, ny, dx=dx):
                moved = True
            elif self._try_step(nx, self.agent_y, dx=dx):
                moved = True
            elif self._try_step(self.agent_x, ny, dx=dx):
                moved = True
            elif self._escape_furniture(float(np.hypot(dx, dy))):
                moved = True
            else:
                hit = self._collision_furniture(self.agent_x, self.agent_y)
                region = "limbs" if not hit or hit.kind != "desk" else "head"
                impulse = biomech.collision_impulse(
                    speed_before=speed_before,
                    region=region,
                    label=hit.label if hit else "",
                )
                pain = float(np.clip(0.03 + impulse * 0.85, 0.03, 0.5))
                events.append({
                    "type": "bump",
                    "region": region,
                    "pain": pain,
                    "target": hit.label if hit else "",
                    "impulse": round(impulse, 3),
                    "physics": True,
                })

        if moved:
            events.append({
                "type": "move",
                "motor": meta.get("gait", "walk"),
                "gait": round(self.gait_phase, 2),
                "speed": meta.get("speed"),
                "physics": True,
            })
            if walk_goal:
                gx, gy = walk_goal
                if float(np.hypot(gx - self.agent_x, gy - self.agent_y)) < 14:
                    self.clear_walk_goal()
        elif walk_goal and not moved and speed_before < 0.5:
            gx, gy = walk_goal
            if float(np.hypot(gx - self.agent_x, gy - self.agent_y)) < 14:
                self.clear_walk_goal()

        if (
            not moved
            and attempted_move
            and any(m in (0, 1, 2, 3) for m in motor)
            and not events
        ):
            hit = self._collision_furniture(self.agent_x, self.agent_y)
            if hit:
                region = "limbs" if hit.kind != "desk" else "head"
                impulse = biomech.collision_impulse(
                    speed_before=max(speed_before, 2.0), region=region
                )
                events.append({
                    "type": "bump",
                    "region": region,
                    "pain": float(np.clip(0.04 + impulse * 0.7, 0.03, 0.45)),
                    "target": hit.label,
                    "physics": True,
                })

        biomech.sync_pose(self.agent_x, self.agent_y)
        biomech.tick_decay()

        if self._attention_target:
            ax, ay = self._attention_target
            if np.hypot(ax - self.agent_x, ay - self.agent_y) < 20:
                self._attention_target = None

        interact = 4 in motor or any(m >= 5 for m in motor)
        if interact:
            ev = self._interact(drives, choice_key=choice_key, brain=brain)
            if ev:
                events.append(ev)

        return {
            "events": events,
            "position": {"x": round(self.agent_x, 1), "y": round(self.agent_y, 1), "dir": self.agent_dir},
            "room": self.current_room(),
            "physics": meta,
        }

    def archetype_card_stats(self) -> dict[str, int]:
        total = touched = internalized = 0
        for obj in self.objects:
            if not is_archetype_card_meta(obj.meta):
                continue
            total += 1
            if obj.meta.get("touched"):
                touched += 1
            if obj.meta.get("internalized"):
                internalized += 1
        return {
            "total": total,
            "untouched": total - touched,
            "uninternalized": total - internalized,
            "internalized": internalized,
        }

    def nearest_archetype_card(
        self,
        max_dist: float = 80.0,
        *,
        require_uninternalized: bool = False,
    ) -> WorldObject | None:
        best, dbest = None, max_dist
        for obj in self.objects:
            if obj.kind != "book" or not is_archetype_card_meta(obj.meta):
                continue
            if require_uninternalized and obj.meta.get("internalized"):
                continue
            d = float(np.hypot(obj.x - self.agent_x, obj.y - self.agent_y))
            if d < dbest:
                dbest, best = d, obj
        return best

    def mark_archetype_internalized(self, obj_id: str, *, personal: str = "") -> None:
        for obj in self.objects:
            if obj.id == obj_id:
                obj.meta["touched"] = True
                obj.meta["internalized"] = True
                if personal:
                    obj.meta["personal_meaning"] = personal[:200]
                return

    def _book_interaction(
        self,
        book: WorldObject,
        drives: dict,
    ) -> dict | None:
        meta = dict(book.meta) if book.meta else {}
        curiosity = drives.get("seek_curiosity", 0)
        if is_archetype_card_meta(meta):
            if curiosity < ARCHETYPE_CARD_TOUCH_THRESHOLD:
                return None
            if meta.get("internalized") and curiosity < ARCHETYPE_CARD_RETOUCH_THRESHOLD:
                return None
            stored = normalize_card_meta(meta)
            return {
                "type": TOUCH_EVENT,
                "object_id": book.id,
                "label": book.label,
                "modality": book.modality,
                "memory_key": book.memory_key,
                "symbol_key": card_key_from_meta(stored),
                "meta": stored,
            }
        if curiosity < BOOK_READ_THRESHOLD and drives.get("seek_stimulus", 0) < 0.4:
            return None
        return {
            "type": "read",
            "object_id": book.id,
            "label": book.label,
            "modality": book.modality,
            "memory_key": book.memory_key,
            "meta": meta,
        }

    def _interact(
        self,
        drives: dict,
        *,
        choice_key: str = "",
        brain=None,
    ) -> dict | None:
        from .behavior_integration import choice_allows_event, pick_desk_study_event

        ck = (choice_key or "").strip()
        amb = self.ambient()
        phase = amb.get("phase", "day")
        hour = int(amb.get("hour", 12))
        at_night = phase == "night" or hour >= 22 or hour < 5
        early = 5 <= hour < 10
        evening = 17 <= hour < 23

        at_desk = (
            self._near_furniture("desk", 55)
            or self._in_zone("desk")
            or self.current_room() == "escritorio"
        )

        def _ok(ev_type: str) -> bool:
            return choice_allows_event(ck, ev_type)

        # PFC eligió estudio/investigación → solo escritorio (navegación lleva antes)
        if ck in ("research", "study", "clinical", "biopsych", "infant"):
            if not at_desk:
                return None
            book = self._nearest_object(max_dist=55.0, kinds={"book"})
            if book and _ok("read"):
                ev = self._book_interaction(book, drives)
                if ev:
                    return ev
            if brain is not None:
                ev = pick_desk_study_event(
                    brain,
                    choice_key=ck,
                    curiosity=float(drives.get("seek_curiosity", 0)),
                )
            else:
                ev = {"type": "web_search" if ck == "research" else "curriculum_study", "target": "escritorio"}
            sk = (ev.get("meta") or {}).get("section_key")
            if sk:
                ev["section_key"] = sk
            return ev

        if ck == "tv" and not (self._near_furniture("tv", 58) or self._in_zone("tv")):
            return None
        if ck in ("eat", "cook", "harvest", "drink") and not (
            self._near_furniture("fridge", 55)
            or self._near_furniture("stove", 54)
            or self._near_furniture("food_bowl", 48)
            or self._near_furniture("fountain", 48)
            or self.current_room() == "jardín"
        ):
            if ck not in ("harvest",) or self.current_room() != "jardín":
                pass  # allow harvest block below
            elif ck == "harvest":
                pass
            elif ck == "drink" and self._near_furniture("fountain", 80):
                pass
            else:
                return None
        if self._near_furniture("toilet", 50) or self._in_zone("toilet"):
            if drives.get("seek_bathroom", 0) > 0.22:
                return {"type": "bathroom", "target": "inodoro"}
        if self._near_furniture("bath", 52) or self._in_zone("bath"):
            if (
                drives.get("seek_hygiene", 0) > 0.2
                or drives.get("seek_bathroom", 0) > 0.35
                or (early and drives.get("seek_hygiene", 0) > 0.12)
            ):
                near = None
                best_d = 1e18
                for fu in self.furniture:
                    if fu.kind != "bath":
                        continue
                    if self.hygiene_only_novel and fu.id in ("bath", "bañera"):
                        continue
                    cx, cy = fu.x + fu.w / 2, fu.y + fu.h / 2
                    d = (cx - self.agent_x) ** 2 + (cy - self.agent_y) ** 2
                    if d <= 52 * 52 and d < best_d:
                        best_d = d
                        near = fu
                if near is not None:
                    return {
                        "type": "bathe",
                        "target": near.label or "bañera",
                        "object_id": near.id,
                        "object_type": "bath",
                    }
        from .food_system import nearest_ripe_crop, pantry_has_cooked, pantry_has_raw
        if self.current_room() == "jardín":
            crop = nearest_ripe_crop(self, 48.0)
            if crop and (
                drives.get("seek_food", 0) > 0.12
                or drives.get("seek_curiosity", 0) > 0.18
            ):
                return {"type": "harvest", "object_id": crop.id, "target": crop.label, "label": crop.label}
        if self._near_furniture("stove", 54) or self._in_zone("stove"):
            if pantry_has_raw(self) and (
                drives.get("seek_cook", 0) > 0.1
                or drives.get("seek_food", 0) > 0.22
            ):
                return {"type": "cook", "target": "cocina"}
            if pantry_has_cooked(self) and drives.get("seek_food", 0) > 0.18:
                return {"type": "eat_cooked", "target": "cocina"}
        # Fuente novel: agua sin schema hardcodeado a nevera.
        if self._near_furniture("fountain", 48) or self._in_zone("fountain"):
            if float(drives.get("seek_water", 0)) > 0.18:
                fu = self._nearest_furniture("fountain", max_dist=48.0) or self._furniture(
                    "fountain"
                )
                oid = fu.id if fu else "novel-fountain"
                return {
                    "type": "drink",
                    "target": fu.label if fu else "fuente",
                    "object_id": oid,
                    "object_type": "fountain",
                    "dry": bool(self.is_object_dry(oid)),
                }
        # Cuenco novel: comida sin GPS a nevera.
        if self._near_furniture("food_bowl", 48) or self._in_zone("food_bowl"):
            if float(drives.get("seek_food", 0)) > 0.18:
                fu = self._furniture("food_bowl")
                return {
                    "type": "eat",
                    "target": fu.label if fu else "cuenco",
                    "object_id": fu.id if fu else "novel-bowl",
                    "object_type": "food_bowl",
                }
        if self._near_furniture("fridge", 55) or self._in_zone("fridge"):
            food_thr = 0.22 if early or evening else 0.32
            food_drive = float(drives.get("seek_food", 0))
            water_drive = float(drives.get("seek_water", 0))
            if (
                (food_drive > food_thr and not self.food_only_novel)
                or (water_drive > 0.3 and not self.water_only_novel)
            ):
                if (
                    not self.water_only_novel
                    and water_drive > max(0.3, food_drive)
                ):
                    return {
                        "type": "drink",
                        "target": "nevera",
                        "object_id": "fridge",
                        "object_type": "fridge",
                    }
                if food_drive > food_thr and not self.food_only_novel:
                    if pantry_has_cooked(self):
                        return {"type": "eat_cooked", "target": "nevera"}
                    return {
                        "type": "eat",
                        "target": "nevera",
                        "object_id": "fridge",
                        "object_type": "fridge",
                    }
                if water_drive > 0.3 and not self.water_only_novel:
                    return {
                        "type": "drink",
                        "target": "nevera",
                        "object_id": "fridge",
                        "object_type": "fridge",
                    }
        if self._near_furniture("bed", 50) or self._in_zone("bed"):
            rest_thr = 0.22 if at_night else 0.38
            sleep_thr = 0.25 if at_night else 0.42
            if drives.get("seek_rest", 0) > rest_thr or drives.get("sleep_need", 0) > sleep_thr:
                fu = self._furniture("bed")
                return {
                    "type": "rest",
                    "target": fu.label if fu else "cama",
                    "object_id": fu.id if fu else "bed",
                    "object_type": "bed",
                }
        if self._near_furniture("tv", 58) or self._in_zone("tv"):
            if at_night and hour >= 1 and hour < 5 and drives.get("seek_stimulus", 0) < 0.55:
                pass
            elif evening or phase == "dusk" or drives.get("seek_stimulus", 0) > 0.15:
                return {"type": "tv_use", "target": "televisión"}
        if at_desk:
            book = self._nearest_object(max_dist=55.0, kinds={"book"})
            if book and _ok("read"):
                ev = self._book_interaction(book, drives)
                if ev:
                    return ev
            if brain is not None:
                ev = pick_desk_study_event(
                    brain,
                    choice_key=ck or "study",
                    curiosity=float(drives.get("seek_curiosity", 0)),
                )
            elif float(drives.get("seek_curiosity", 0)) > 0.25:
                ev = {"type": "web_search", "target": "escritorio"}
            else:
                ev = {"type": "curriculum_study", "target": "escritorio"}
            if not _ok(str(ev.get("type", ""))):
                return None
            sk = (ev.get("meta") or {}).get("section_key")
            if sk:
                ev["section_key"] = sk
            return ev
        if (
            self.current_room() in ("escritorio", "sala_tv", "casa")
            and drives.get("seek_curiosity", 0) > 0.35
            and _ok("web_search")
        ):
            return {"type": "web_search", "target": "internet"}
        book = self._nearest_object(max_dist=35.0, kinds={"book"})
        if book:
            ev = self._book_interaction(book, drives)
            if ev:
                return ev
        obj = self._nearest_object(max_dist=32.0)
        if obj:
            return {
                "type": "touch",
                "object_id": obj.id,
                "label": obj.label,
                "modality": obj.modality,
                "memory_key": obj.memory_key,
            }
        if drives.get("seek_stimulus", 0) > 0.3 and self._near_furniture("tv", 80):
            return {"type": "tv_use", "target": "televisión"}
        return None

    def _near_furniture(self, kind: str, dist: float) -> bool:
        """True si hay algún mueble de ``kind`` a menos de ``dist`` del agente."""
        for fu in self.furniture:
            if fu.kind != kind:
                continue
            cx, cy = fu.x + fu.w / 2, fu.y + fu.h / 2
            if float(np.hypot(self.agent_x - cx, self.agent_y - cy)) < dist:
                return True
        return False

    def _nearest_object(self, max_dist: float, kinds: set[str] | None = None) -> WorldObject | None:
        best, dbest = None, max_dist
        for obj in self.objects:
            if kinds and obj.kind not in kinds:
                continue
            d = float(np.hypot(obj.x - self.agent_x, obj.y - self.agent_y))
            if d < dbest:
                dbest, best = d, obj
        return best

    def set_web_session(self, *, query: str, provider: str, results: list[dict]) -> None:
        self.web_state = {
            "active": bool(results),
            "query": query[:80],
            "provider": provider[:24],
            "results": [
                {
                    "title": r.get("title", "")[:120],
                    "url": r.get("url", "")[:240],
                    "snippet": r.get("snippet", "")[:240],
                }
                for r in results[:6]
            ],
        }

    def set_tv_playing(self, *, query: str, title: str, video_id: str, url: str) -> None:
        self.tv_state = {
            "active": True,
            "query": query[:80],
            "title": title[:120],
            "video_id": video_id,
            "url": url,
        }

    def visible_objects(self) -> list[dict]:
        out = []
        for obj in self.objects:
            d = float(np.hypot(obj.x - self.agent_x, obj.y - self.agent_y))
            if d <= self.view_radius * 1.2:
                out.append(
                    {
                        "id": obj.id,
                        "kind": obj.kind,
                        "label": obj.label,
                        "modality": obj.modality,
                        "distance": round(d, 1),
                    }
                )
        for fu in self.furniture:
            cx, cy = fu.x + fu.w / 2, fu.y + fu.h / 2
            d = float(np.hypot(cx - self.agent_x, cy - self.agent_y))
            if d <= self.view_radius * 1.3:
                out.append({"kind": fu.kind, "label": fu.label, "distance": round(d, 1)})
        return out

    def to_dict(self) -> dict:
        amb = self.ambient()
        from .material_qualities import furniture_qualities, object_qualities

        room_temp = self.room_temperature()
        stove_hot = any(not p.get("raw") for p in self.pantry if isinstance(p, dict))
        base = {
            "width": self.width,
            "height": self.height,
            "agent": {
                "x": round(self.agent_x, 1),
                "y": round(self.agent_y, 1),
                "dir": self.agent_dir,
                "gait_phase": round(self.gait_phase, 3),
                "walking": self.is_walking,
            },
            "room": self.current_room(),
            "room_temp": round(self.room_temperature(), 3),
            "environment": amb,
            "hero_zone": amb["hero_zone"],
            "objects": [
                {
                    "id": o.id,
                    "kind": o.kind,
                    "x": round(o.x, 1),
                    "y": round(o.y, 1),
                    "label": o.label,
                    "modality": o.modality,
                    "zone": o.zone,
                    "meta": normalize_card_meta(o.meta),
                    "qualities": object_qualities(o.kind, normalize_card_meta(o.meta)),
                }
                for o in self.objects
            ],
            "furniture": [
                {
                    "id": f.id,
                    "kind": f.kind,
                    "x": f.x,
                    "y": f.y,
                    "w": f.w,
                    "h": f.h,
                    "label": f.label,
                    "qualities": furniture_qualities(
                        f.kind,
                        room_temp=room_temp,
                        tv_active=bool(self.tv_state.get("active")),
                        web_active=bool(self.web_state.get("active")),
                        stove_hot=stove_hot,
                    ),
                }
                for f in self.furniture
            ],
            "trees": self.trees,
            "pantry": list(self.pantry),
            "tv": dict(self.tv_state),
            "web": dict(self.web_state),
            "visible": self.visible_objects(),
            "archetype_cards": self.archetype_card_stats(),
        }
        return base

    def with_companion(self, companion_dict: dict | None) -> dict:
        d = self.to_dict()
        if companion_dict:
            d["companion"] = companion_dict
        return d


def kind_from_modality(modality: str) -> str:
    return {
        "image": "item",
        "document": "book",
        "text": "book",
        "audio": "item",
        "social": "sign",
        "video": "screen",
    }.get(modality, "item")
