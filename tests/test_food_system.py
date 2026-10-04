"""Cosecha, despensa y cocina."""

from brain.food_system import (
    cook_meal,
    ensure_garden_crops,
    ensure_stove,
    harvest_crop,
    pantry_has_cooked,
    pantry_has_raw,
    tick_crops,
)
from brain.world import World2D


def test_garden_crops_and_harvest():
    w = World2D()
    w.ensure_home()
    ensure_garden_crops(w)
    assert any(o.kind == "crop" for o in w.objects)
    crop = next(o for o in w.objects if o.kind == "crop")
    w.agent_x, w.agent_y = crop.x, crop.y
    result = harvest_crop(w, crop.id)
    assert result is not None
    assert pantry_has_raw(w)
    assert crop.meta["ripe"] is False
    assert crop.meta["regrow_ticks"] > 0


def test_cook_and_eat_flow():
    w = World2D()
    w.ensure_home()
    ensure_garden_crops(w)
    ensure_stove(w)
    crop = next(o for o in w.objects if o.kind == "crop")
    harvest_crop(w, crop.id)
    cooked = cook_meal(w)
    assert cooked is not None
    assert not pantry_has_raw(w)
    assert pantry_has_cooked(w)


def test_crop_regrowth():
    w = World2D()
    w.ensure_home()
    ensure_garden_crops(w)
    crop = next(o for o in w.objects if o.kind == "crop")
    harvest_crop(w, crop.id)
    ticks = int(crop.meta["regrow_ticks"])
    for _ in range(ticks):
        tick_crops(w)
    assert crop.meta["ripe"] is True
