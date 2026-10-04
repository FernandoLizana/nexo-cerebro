"""Terminal nociceptivo y contacto somático emergente."""

from __future__ import annotations

from brain.body import BodyState
from brain.nociception import NociceptiveTerminal
from brain.somatic_affordances import apply_somatic_contact, furniture_contact
from brain.world import World2D


def test_nociceptor_collision_projects_pain():
    body = BodyState()
    noc = NociceptiveTerminal()
    noc.apply_collision("limbs", 0.25, label="mesa")
    noc._project_to_body(body)
    assert body.pain_limbs > 0.08
    assert noc.a_delta["limbs"] > 0.05


def test_nociceptor_tick_from_hunger():
    body = BodyState(hunger=0.9)
    noc = NociceptiveTerminal()
    noc.tick(body, room_temp=0.5)
    assert noc.c_fiber.get("viscera", 0) > 0 or body.pain_ache > 0


def test_gate_inhibition_reduces_pain():
    body = BodyState()
    noc = NociceptiveTerminal()
    noc.apply_collision("limbs", 0.4)
    noc._project_to_body(body)
    before = body.pain_limbs
    noc.gate_inhibition(0.3)
    noc._project_to_body(body)
    assert body.pain_limbs < before


def test_sofa_contact_raises_comfort_without_navigation():
    world = World2D()
    world.ensure_home()
    sofa = next(f for f in world.furniture if f.kind == "sofa")
    world.agent_x = sofa.x + sofa.w / 2
    world.agent_y = sofa.y + sofa.h / 2
    body = BodyState(comfort=0.4, fatigue=0.6)
    assert furniture_contact(world) is not None
    result = apply_somatic_contact(world, body)
    assert result and result["kind"] == "sofa"
    assert body.comfort > 0.4
    assert body.fatigue < 0.6


def test_no_somatic_contact_when_away_from_furniture():
    world = World2D()
    world.ensure_home()
    world.agent_x = 50
    world.agent_y = 50
    body = BodyState()
    assert apply_somatic_contact(world, body) is None
