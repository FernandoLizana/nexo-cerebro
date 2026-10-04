"""Tests material_qualities — cualidades físicas de muebles."""

from __future__ import annotations

from brain.material_qualities import furniture_qualities, object_qualities


def test_fridge_is_cold():
    q = furniture_qualities("fridge", room_temp=21.0)
    assert q["temperature_c"] < 12
    assert "frío" in q["feels"].lower()


def test_stove_hot_when_cooking_context():
    q = furniture_qualities("stove", stove_hot=True)
    assert q["temperature_c"] > 50
    assert q.get("emissive")


def test_crop_qualities():
    q = object_qualities("crop", {"food": "tomate", "ripe": True})
    assert q["label_food"] == "tomate"
