"""Movimiento y desbloqueo del agente en el hogar."""

from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE


def test_agent_unstuck_from_furniture():
    brain = InfantApeBrain()
    brain.world.agent_x = 358.5
    brain.world.agent_y = 237.0
    assert brain.world._collision_furniture(brain.world.agent_x, brain.world.agent_y)
    assert brain.world.ensure_agent_free()
    assert not brain.world._collision_furniture(brain.world.agent_x, brain.world.agent_y)


def test_agent_moves_after_unstuck():
    brain = InfantApeBrain()
    brain.world.agent_x = 358.5
    brain.world.agent_y = 237.0
    brain.world.ensure_agent_free()
    x0, y0 = brain.world.agent_x, brain.world.agent_y
    brain.world.set_walk_goal(567.5, 312.5)
    moved = brain.world.apply_motor([], drives=brain._merged_drives())
    assert moved["events"] or (brain.world.agent_x, brain.world.agent_y) != (x0, y0)


def test_biomechanics_keeps_subpixel_motion_without_false_collision():
    brain = InfantApeBrain(profile=COMPACT_PROFILE, headless=True, auto_save=False)
    brain.world.ensure_home()
    brain.world.agent_x = 500.0
    brain.world.agent_y = 80.0
    brain.world.ensure_agent_free()
    x0, y0 = brain.world.agent_x, brain.world.agent_y
    brain.world.set_walk_goal(420.0, 160.0)

    result = brain.world.apply_motor(
        [],
        drives=brain._merged_drives(),
        biomech=brain.biomech,
    )

    assert (brain.world.agent_x, brain.world.agent_y) != (x0, y0)
    assert not any(event.get("type") == "bump" for event in result["events"])
