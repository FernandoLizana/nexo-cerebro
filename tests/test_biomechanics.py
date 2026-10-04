"""Física y biomecánica corporal."""

from __future__ import annotations

from brain.biomechanics import BiomechanicalBody
from brain.body import BodyState
from brain.nociception import NociceptiveTerminal
from brain.world import World2D


def test_physics_movement_and_friction():
    world = World2D()
    world.ensure_home()
    world.agent_x, world.agent_y = 240.0, 230.0
    bio = BiomechanicalBody()
    bio.vx, bio.vy = 8.0, 0.0
    dx, dy, meta = bio.integrate(world, [])
    assert meta["gait"] in ("walk", "run", "idle")
    bio.tick_decay()
    assert bio.vx < 8.0 or dx != 0


def test_collision_impulse_and_ragdoll():
    bio = BiomechanicalBody()
    bio.vx, bio.vy = 12.0, 0.0
    impulse = bio.collision_impulse(speed_before=12.0, region="limbs")
    assert impulse > 0.02
    assert bio.vx < 0
    assert bio.joint_stress["knee_l"] > 0


def test_biomech_feeds_body_and_nociception():
    body = BodyState(fatigue=0.3)
    noc = NociceptiveTerminal()
    bio = BiomechanicalBody()
    bio.physical_fatigue = 0.6
    bio.joint_stress["knee_l"] = 0.55
    bio.apply_to_interoception(body, noc)
    assert body.fatigue >= 0.3
    assert noc.c_fiber.get("limbs", 0) > 0 or body.pain_limbs > 0


def test_world_physics_motor():
    world = World2D()
    world.ensure_home()
    world.agent_x, world.agent_y = 240.0, 230.0
    bio = BiomechanicalBody()
    result = world.apply_motor([1], drives={}, biomech=bio)
    assert "events" in result
    assert result.get("physics") is not None
    assert "bones" in bio.to_dict()


def test_spinal_shock_propagation():
    from brain.ragdoll_skeleton import ArticulatedSkeleton

    sk = ArticulatedSkeleton()
    sk.inject_spinal_shock(0.8, entry=0)
    peak = sk.propagate_spine()
    assert peak > 0.1
    assert sk.spine_shock[1] > 0 or sk.spine_shock[2] > 0
    assert "spine" in sk.joint_stress_map()


def test_water_buoyancy():
    world = World2D()
    world.ensure_home()
    bath = world._furniture("bath")
    assert bath
    world.agent_x = bath.x + bath.w / 2
    world.agent_y = bath.y + bath.h / 2
    bio = BiomechanicalBody()
    bio.integrate(world, [])
    assert bio.in_water
    assert bio.water_depth > 0.4
    assert bio.buoyancy_n > 100
