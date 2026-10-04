"""
Sistema alimentario — cosecha en jardín, despensa y cocina.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .world import World2D, WorldObject

CROP_SPECS: tuple[dict[str, Any], ...] = (
    {"food": "tomate", "label": "tomates", "x": 48, "y": 72, "value": 0.32},
    {"food": "lechuga", "label": "lechuga", "x": 88, "y": 118, "value": 0.28},
    {"food": "zanahoria", "label": "zanahorias", "x": 28, "y": 155, "value": 0.3},
    {"food": "fresa", "label": "fresas", "x": 118, "y": 88, "value": 0.26},
    {"food": "albahaca", "label": "albahaca", "x": 72, "y": 185, "value": 0.22},
    {"food": "calabaza", "label": "calabaza", "x": 135, "y": 145, "value": 0.38},
)


def ensure_garden_crops(world: World2D) -> None:
    """Parcelas cosechables en el patio."""
    existing = {o.id for o in world.objects if o.kind == "crop"}
    for i, spec in enumerate(CROP_SPECS):
        oid = f"crop-{spec['food']}"
        if oid in existing:
            continue
        world.objects.append(
            WorldObject(
                id=oid,
                kind="crop",
                x=float(spec["x"]),
                y=float(spec["y"]),
                label=spec["label"],
                modality="world",
                memory_key=f"crop:{spec['food']}",
                radius=18.0,
                zone="garden",
                meta={
                    "harvestable": True,
                    "ripe": True,
                    "food": spec["food"],
                    "food_value": spec["value"],
                    "raw": True,
                    "regrow_ticks": 0,
                },
            )
        )


def ensure_stove(world: World2D) -> None:
    from .world import Furniture

    if not any(f.kind == "stove" for f in world.furniture):
        world.furniture.append(
            Furniture("stove", "stove", 285, 278, 52, 58, "cocina")
        )


def nearest_ripe_crop(world: World2D, max_dist: float = 55.0) -> WorldObject | None:
    best, best_d = None, 1e9
    for obj in world.objects:
        if obj.kind != "crop":
            continue
        if not obj.meta.get("ripe", True):
            continue
        d = float(np.hypot(obj.x - world.agent_x, obj.y - world.agent_y))
        if d < max_dist and d < best_d:
            best_d, best = d, obj
    return best


def has_ripe_crops(world: World2D) -> bool:
    return any(o.kind == "crop" and o.meta.get("ripe") for o in world.objects)


def pantry_has_raw(world: World2D) -> bool:
    return any(p.get("raw") for p in world.pantry)


def pantry_has_cooked(world: World2D) -> bool:
    return any(not p.get("raw") for p in world.pantry)


def harvest_crop(world: World2D, object_id: str) -> dict[str, Any] | None:
    obj = next((o for o in world.objects if o.id == object_id), None)
    if not obj or obj.kind != "crop" or not obj.meta.get("ripe"):
        return None
    food = str(obj.meta.get("food", "cosecha"))
    amount = float(obj.meta.get("food_value", 0.3))
    world.pantry.append({
        "food": food,
        "label": obj.label,
        "amount": amount,
        "raw": True,
    })
    obj.meta["ripe"] = False
    obj.meta["regrow_ticks"] = 48
    return {"food": food, "label": obj.label, "amount": amount, "raw": True}


def tick_crops(world: World2D) -> None:
    for obj in world.objects:
        if obj.kind != "crop" or obj.meta.get("ripe"):
            continue
        t = int(obj.meta.get("regrow_ticks", 0))
        if t > 0:
            obj.meta["regrow_ticks"] = t - 1
            if obj.meta["regrow_ticks"] == 0:
                obj.meta["ripe"] = True
        else:
            obj.meta["ripe"] = True


def cook_meal(world: World2D) -> dict[str, Any] | None:
    raw_idx = next((i for i, p in enumerate(world.pantry) if p.get("raw")), None)
    if raw_idx is None:
        return None
    item = world.pantry.pop(raw_idx)
    cooked = {
        "food": item["food"],
        "label": f"{item['label']} cocida",
        "amount": float(item.get("amount", 0.3)) * 1.15,
        "raw": False,
        "pleasure_bonus": 0.42,
    }
    world.pantry.append(cooked)
    return cooked


def eat_cooked(world: World2D) -> dict[str, Any] | None:
    idx = next((i for i, p in enumerate(world.pantry) if not p.get("raw")), None)
    if idx is not None:
        return world.pantry.pop(idx)
    return None


def eat_raw(world: World2D) -> dict[str, Any] | None:
    idx = next((i for i, p in enumerate(world.pantry) if p.get("raw")), None)
    if idx is None:
        return None
    item = world.pantry.pop(idx)
    item["pleasure_bonus"] = 0.12
    return item


def pantry_dict(world: World2D) -> dict[str, Any]:
    return {
        "items": list(world.pantry),
        "raw_count": sum(1 for p in world.pantry if p.get("raw")),
        "cooked_count": sum(1 for p in world.pantry if not p.get("raw")),
    }
