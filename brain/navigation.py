"""Navegación por impulsos internos — sin órdenes del cuidador."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .curiosity import ARCHETYPE_CARD_TOUCH_THRESHOLD, BOOK_READ_THRESHOLD
from .food_system import has_ripe_crops, nearest_ripe_crop, pantry_has_cooked, pantry_has_raw

if TYPE_CHECKING:
    from .world import World2D

LOCOMOTION = frozenset({0, 1, 2, 3})
INTERACT_CODE = 4


def decode_cortex_motor(motor: list[int]) -> list[int]:
    """Traduce índices corticales (0–N) a direcciones del mundo (0–3) + interact (4)."""
    out: list[int] = []
    seen: set[int] = set()
    for m in motor:
        if m == INTERACT_CODE:
            if INTERACT_CODE not in seen:
                out.append(INTERACT_CODE)
                seen.add(INTERACT_CODE)
        elif m in LOCOMOTION:
            if m not in seen:
                out.append(m)
                seen.add(m)
        else:
            d = int(m) % 4
            if d not in seen:
                out.append(d)
                seen.add(d)
    return out


def augment_motor(
    world: World2D,
    motor: list[int],
    drives: dict,
    *,
    companion_xy: tuple[float, float] | None = None,
    ambient: dict | None = None,
) -> list[int]:
    """Añade dirección hacia metas (comida, calor, compañera) sin sustituir el motor neural."""
    amb = ambient or world.ambient()
    extra: list[int] = []
    room = world.current_room()
    # Prioriza walk_goal activo (affordance / goal_stack) sobre heurística de drives.
    if world._walk_goal is not None:
        tx, ty = world._walk_goal
        extra.extend(_bearing_motors(world.agent_x, world.agent_y, tx, ty))
    else:
        goal = _drive_goal(world, drives, room, companion_xy=companion_xy, ambient=amb)
        if goal is not None:
            tx, ty = goal
            extra.extend(_bearing_motors(world.agent_x, world.agent_y, tx, ty))
    if room == "jardín" and world.agent_x < 172:
        hour = int(amb.get("hour", 12))
        if hour >= 22 or hour < 6:
            extra.append(1)
    if world._attention_target:
        ax, ay = world._attention_target
        extra.extend(_bearing_motors(world.agent_x, world.agent_y, ax, ay))

    merged = list(dict.fromkeys(extra + list(motor)))
    if _should_interact(world, drives, amb):
        if INTERACT_CODE not in merged:
            merged.insert(0, INTERACT_CODE)
    if not any(m in LOCOMOTION for m in merged):
        merged = _explore_step(world, merged)
    return merged[:8]


def _explore_step(world: World2D, motor: list[int]) -> list[int]:
    """Deambular cuando no hay meta clara."""
    seed = int(world.agent_x * 0.7 + world.agent_y * 0.3) // 12
    return [seed % 4] + list(motor)


def _drive_goal(
    world: World2D,
    drives: dict,
    room: str,
    *,
    companion_xy: tuple[float, float] | None = None,
    ambient: dict | None = None,
) -> tuple[float, float] | None:
    amb = ambient or {}
    phase = amb.get("phase", "day")
    hour = int(amb.get("hour", 12))
    at_night = phase == "night" or hour >= 22 or hour < 5

    if at_night and (
        drives.get("sleep_need", 0) > 0.28
        or drives.get("seek_rest", 0) > 0.32
    ):
        bed = world.furniture_center("bed")
        if bed:
            return bed

    if drives.get("seek_bathroom", 0) > 0.32:
        c = world.furniture_center("toilet")
        if c:
            return c
    if drives.get("seek_hygiene", 0) > 0.3:
        if getattr(world, "hygiene_only_novel", False):
            return None
        c = world.furniture_center("bath")
        if c:
            return c
    if drives.get("seek_warmth", 0) > 0.25 and room == "jardín":
        return 240.0, 220.0
    if drives.get("seek_cook", 0) > 0.2 and pantry_has_raw(world):
        c = world.furniture_center("stove")
        if c:
            return c
    if room == "jardín" and (
        drives.get("seek_food", 0) > 0.18
        or drives.get("seek_curiosity", 0) > 0.22
    ):
        if has_ripe_crops(world):
            crop = nearest_ripe_crop(world, 999.0)
            if crop:
                return crop.x, crop.y
    if drives.get("seek_food", 0) > 0.28 or (5 <= hour < 10 and drives.get("seek_food", 0) > 0.18):
        # Arena novel: sin GPS gratis; el prior llega por affordance_food_xy.
        if getattr(world, "food_only_novel", False):
            return None
        if pantry_has_cooked(world):
            c = world.furniture_center("stove") or world.furniture_center("fridge")
        else:
            c = world.furniture_center("fridge")
        if c:
            return c
    if drives.get("seek_water", 0) > 0.35:
        # Arena novel: sin GPS gratis; el prior fuerte llega por affordance_water_xy.
        if getattr(world, "water_only_novel", False):
            return None
        c = world.furniture_center("fountain") or world.furniture_center("fridge")
        if c:
            return c
    # descanso / estímulo / confort: sin meta a cama/TV/sofá — emerge del contacto somático
    if drives.get("seek_companion", 0) > 0.22 and companion_xy:
        return companion_xy
    curiosity = drives.get("seek_curiosity", 0)
    if curiosity > 0.36:
        desk = world.furniture_center("desk")
        if desk and room != "escritorio":
            return desk
    if curiosity > ARCHETYPE_CARD_TOUCH_THRESHOLD and not at_night:
        card = world.nearest_archetype_card(max_dist=120.0, require_uninternalized=True)
        if card:
            return card.x, card.y
        desk = world.furniture_center("desk")
        if desk and room != "escritorio":
            return desk
    if room == "jardín" and drives.get("seek_stimulus", 0) > 0.15 and not at_night:
        c = world.furniture_center("tv")
        if c:
            return c
    return None


def _bearing_motors(x: float, y: float, tx: float, ty: float) -> list[int]:
    out: list[int] = []
    if tx - x > 10:
        out.append(1)
    elif tx - x < -10:
        out.append(0)
    if ty - y > 10:
        out.append(3)
    elif ty - y < -10:
        out.append(2)
    return out


def _should_interact(world: World2D, drives: dict, ambient: dict | None = None) -> bool:
    amb = ambient or {}
    hour = int(amb.get("hour", 12))
    at_night = amb.get("phase") == "night" or hour >= 22 or hour < 5
    curiosity = drives.get("seek_curiosity", 0)
    if world._near_furniture("tv", 52):
        if at_night and hour >= 1 and hour < 5:
            return drives.get("seek_stimulus", 0) > 0.55
        return drives.get("seek_stimulus", 0) > 0.15 or 17 <= hour < 23
    if world.current_room() == "jardín":
        crop = nearest_ripe_crop(world, 50.0)
        if crop and (
            drives.get("seek_food", 0) > 0.14
            or drives.get("seek_curiosity", 0) > 0.2
        ):
            return True
    if world._near_furniture("stove", 52):
        if drives.get("seek_cook", 0) > 0.12 and pantry_has_raw(world):
            return True
        if pantry_has_cooked(world) and drives.get("seek_food", 0) > 0.2:
            return True
    if world._near_furniture("fountain", 46):
        return drives.get("seek_water", 0) > 0.2
    if world._near_furniture("food_bowl", 46):
        return drives.get("seek_food", 0) > 0.2
    if world._near_furniture("fridge", 48):
        food_thr = 0.22 if 5 <= hour < 10 else 0.3
        if getattr(world, "food_only_novel", False):
            return False
        if getattr(world, "water_only_novel", False):
            return drives.get("seek_food", 0) > food_thr
        return drives.get("seek_food", 0) > food_thr or drives.get("seek_water", 0) > 0.35
    if world._near_furniture("bath", 48):
        if getattr(world, "hygiene_only_novel", False):
            for fu in world.furniture:
                if fu.kind == "bath" and fu.id not in ("bath", "bañera"):
                    cx, cy = fu.x + fu.w / 2, fu.y + fu.h / 2
                    if (cx - world.agent_x) ** 2 + (cy - world.agent_y) ** 2 <= 48 * 48:
                        return drives.get("seek_hygiene", 0) > 0.22
            return False
        return drives.get("seek_hygiene", 0) > 0.28 or drives.get("seek_bathroom", 0) > 0.38
    if world._near_furniture("toilet", 46):
        return drives.get("seek_bathroom", 0) > 0.28
    if world._near_furniture("bed", 45):
        rest_thr = 0.22 if at_night else 0.38
        return drives.get("seek_rest", 0) > rest_thr or drives.get("sleep_need", 0) > 0.3
    if world._near_furniture("desk", 50):
        if at_night and curiosity < ARCHETYPE_CARD_TOUCH_THRESHOLD + 0.15:
            return False
        card = world.nearest_archetype_card(max_dist=55.0, require_uninternalized=True)
        if card and curiosity > ARCHETYPE_CARD_TOUCH_THRESHOLD:
            return True
        if world._nearest_object(40, kinds={"book"}) and curiosity > BOOK_READ_THRESHOLD:
            return True
        if curiosity > 0.36:
            return True
        if curiosity > 0.28:
            return True
    return False


def resolve_walk_goal(
    world: World2D,
    drives: dict,
    *,
    companion_xy: tuple[float, float] | None = None,
    ambient: dict | None = None,
    goal_stack=None,
    affordance_water_xy: tuple[float, float] | None = None,
    affordance_food_xy: tuple[float, float] | None = None,
    affordance_hygiene_xy: tuple[float, float] | None = None,
) -> tuple[float, float] | None:
    """Meta de caminata continua hacia mueble u objetivo."""
    room = world.current_room()
    if goal_stack is not None:
        top = goal_stack.peek()
        if top and top.phase == "navigate" and top.target:
            target = str(top.target)
            skip_fridge_gps = (
                (
                    getattr(world, "water_only_novel", False)
                    and top.choice_key == "drink"
                    and target == "fridge"
                )
                or (
                    getattr(world, "food_only_novel", False)
                    and top.choice_key == "eat"
                    and target == "fridge"
                )
            )
            skip_bath_gps = (
                getattr(world, "hygiene_only_novel", False)
                and top.choice_key == "hygiene"
                and target == "bath"
            )
            if not skip_fridge_gps and not skip_bath_gps:
                # Remap nevera→fuente solo fuera de arena novel (evita GPS gratis).
                if (
                    target == "fridge"
                    and world._furniture("fountain") is not None
                ):
                    if top.choice_key == "drink" or float(drives.get("seek_water", 0)) >= float(
                        drives.get("seek_food", 0)
                    ):
                        fountain = world.furniture_center("fountain")
                        if fountain:
                            return fountain
                c = world.furniture_center(target)
                if c:
                    return c
    # Evidencia causal: si hay affordance de beber/comer/higiene confiable, prioriza ese objeto.
    if affordance_water_xy is not None and drives.get("seek_water", 0) > 0.28:
        return affordance_water_xy
    if affordance_food_xy is not None and drives.get("seek_food", 0) > 0.28:
        return affordance_food_xy
    if affordance_hygiene_xy is not None and drives.get("seek_hygiene", 0) > 0.28:
        return affordance_hygiene_xy
    goal = _drive_goal(world, drives, room, companion_xy=companion_xy, ambient=ambient)
    if goal:
        return goal
    if world._attention_target:
        return world._attention_target
    return None
