"""S5 — TextWorld tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from nexo.core.environment_protocol import EnvironmentProtocol, action_schemas_for

from services.being.creator import create_being
from services.being.models import BeingArchetype, BeingSpecies
from services.worlds.textworld.runner import run_textworld_experiment
from services.worlds.textworld.world import TextWorld


def _two_beings():
    a = create_being(
        name="Alpha",
        species=BeingSpecies.HUMANOID,
        archetype=BeingArchetype.EXPLORER,
        creator_node="n",
        traits={"sociability": 0.9, "curiosity": 0.8, "exploration": 0.7},
    )
    b = create_being(
        name="Beta",
        species=BeingSpecies.ANIMAL,
        archetype=BeingArchetype.DOG,
        creator_node="n",
        traits={"sociability": 0.85, "curiosity": 0.6},
    )
    # Force stable ids for cross-run comparison by rewriting after create is awkward;
    # runner sorts by being_id, so we compare fingerprints with same beings objects cloned via traits.
    return a, b


def test_seeded_replay_identical_fingerprint() -> None:
    a1, b1 = _two_beings()
    a2 = create_being(
        name="Alpha",
        species=BeingSpecies.HUMANOID,
        archetype=BeingArchetype.EXPLORER,
        creator_node="n",
        traits=dict(a1.identity.core_personality.traits),
    )
    b2 = create_being(
        name="Beta",
        species=BeingSpecies.ANIMAL,
        archetype=BeingArchetype.DOG,
        creator_node="n",
        traits=dict(b1.identity.core_personality.traits),
    )
    # Overwrite ids to match so placement/order/actions align.
    a2.identity.being_id = a1.identity.being_id
    b2.identity.being_id = b1.identity.being_id

    r1 = run_textworld_experiment(
        [a1, b1],
        seed=42,
        ticks=25,
        initial_places={a1.identity.being_id: "meadow", b1.identity.being_id: "meadow"},
    )
    r2 = run_textworld_experiment(
        [b2, a2],  # shuffled input order
        seed=42,
        ticks=25,
        initial_places={a2.identity.being_id: "meadow", b2.identity.being_id: "meadow"},
    )
    assert r1["trace_fingerprint"] == r2["trace_fingerprint"]
    assert r1["interaction_count"] == r2["interaction_count"]
    assert r1["snapshot"]["locations"] == r2["snapshot"]["locations"]


def test_environment_protocol_agent_view() -> None:
    world = TextWorld(seed=1)
    world.place_being("being-x", "den")
    view = world.agent_view("being-x")
    assert isinstance(view, EnvironmentProtocol)
    actions = view.available_actions()
    assert "observe" in actions
    assert any(a.startswith("move_") for a in actions)
    schemas = action_schemas_for(view)
    assert {s.id for s in schemas} == set(actions)
    raw = view.apply_action("observe")
    assert raw["accepted"] is True


def test_interaction_events_emitted() -> None:
    a, b = _two_beings()
    result = run_textworld_experiment(
        [a, b],
        seed=7,
        ticks=30,
        initial_places={a.identity.being_id: "clearing", b.identity.being_id: "clearing"},
    )
    types = {e["event_type"] for e in result["events"]}
    assert "BEING_INTERACTION" in types
    assert "WORLD_TICK" in types
    assert result["interaction_count"] >= 1


def test_node_textworld_job(tmp_path: Path) -> None:
    from services.node.jobs import JobRequest
    from services.node.runtime import NodeRuntime

    runtime = NodeRuntime(data_dir=tmp_path / "node", node_name="unit")
    runtime.start()
    ids = []
    for name, species, arch in (("One", "HUMANOID", "EXPLORER"), ("Two", "ANIMAL", "DOG")):
        created = runtime.submit_job(
            JobRequest(
                job_type="CREATE_BEING",
                job_id=f"mk-{name}",
                payload={"name": name, "species": species, "archetype": arch},
            )
        )
        ids.append(created["result"]["being"]["being_id"])
    result = runtime.submit_job(
        JobRequest(
            job_type="RUN_TEXTWORLD_EXPERIMENT",
            job_id="tw1",
            payload={"being_ids": ids, "ticks": 12, "seed": 3, "co_locate": "meadow"},
        )
    )
    assert result["ok"] is True
    assert result["result"]["ok"] is True
    assert result["result"]["trace_fingerprint"]
