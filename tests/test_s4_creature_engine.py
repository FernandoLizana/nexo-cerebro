"""S4 — Creature Engine tests (no LLM, deterministic ticks)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from services.being.creator import create_being
from services.being.models import BeingArchetype, BeingSpecies
from services.creature.engine import CreatureEngine, run_creature_ticks
from services.creature.fsm import CreatureState, can_transition
from services.creature.memory import AssociativeMemory


ROOT = Path(__file__).resolve().parents[1]
CREATURE_PKG = ROOT / "services" / "creature"


def _dog(tmp_name: str = "Bolt"):
    return create_being(
        name=tmp_name,
        species=BeingSpecies.ANIMAL,
        archetype=BeingArchetype.DOG,
        creator_node="test-node",
        use_llm=False,
    )


def test_deterministic_trajectory() -> None:
    a = _dog("A")
    b = _dog("B")
    # Same seed + identical initial drives/personality → identical trajectory shape.
    # Distinct being_ids don't affect RNG; copy drives from a to b for fairness.
    b.state.drives = dict(a.state.drives)
    b.identity.core_personality = a.identity.core_personality
    ra = run_creature_ticks(a, ticks=40, seed=123)
    rb = run_creature_ticks(b, ticks=40, seed=123)
    assert ra["llm_used"] is False
    assert [t["action"] for t in ra["trajectory"]] == [t["action"] for t in rb["trajectory"]]
    assert ra["final_drives"] == rb["final_drives"]


def test_hunger_and_energy_dynamics() -> None:
    being = _dog()
    being.state.drives["hunger"] = 0.9
    being.state.drives["energy"] = 0.2
    engine = CreatureEngine(being=being, seed=7)
    # Force food-rich path by learning and ticking
    results = [engine.step() for _ in range(25)]
    hungers = [r.drives["hunger"] for r in results]
    energies = [r.drives["energy"] for r in results]
    assert all(0.0 <= h <= 1.0 for h in hungers)
    assert all(0.0 <= e <= 1.0 for e in energies)
    # With high hunger, forage/eat should appear
    actions = {r.action for r in results}
    assert actions & {"FORAGE", "EAT", "REST", "EXPLORE", "IDLE", "FLEE", "SOCIALIZE", "INSPECT"}


def test_refuses_llm_being() -> None:
    being = create_being(
        name="Chatty",
        species=BeingSpecies.HUMANOID,
        creator_node="n",
        use_llm=True,
    )
    with pytest.raises(ValueError, match="use_llm"):
        CreatureEngine(being=being, seed=1)


def test_associative_memory_learn_recall_decay() -> None:
    mem = AssociativeMemory()
    mem.learn("threat", "flee", 0.5)
    resp, strength = mem.recall("threat")
    assert resp == "flee"
    assert strength >= 0.5
    mem.decay(0.5)
    _, strength2 = mem.recall("threat")
    assert strength2 < strength


def test_fsm_transitions() -> None:
    assert can_transition(CreatureState.IDLE, CreatureState.FORAGE)
    assert not can_transition(CreatureState.EAT, CreatureState.SOCIALIZE)


def test_no_llm_imports_in_creature_package() -> None:
    forbidden = ("openai", "ollama", "anthropic", "transformers", "torch", "llama")
    for path in CREATURE_PKG.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for token in forbidden:
            assert token not in text, f"{path} mentions {token}"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in {"socket", "subprocess", "requests"}
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in {"socket", "subprocess", "requests"}


def test_node_run_creature_simulation_job(tmp_path: Path) -> None:
    from services.node.jobs import JobRequest
    from services.node.runtime import NodeRuntime

    runtime = NodeRuntime(data_dir=tmp_path / "node", node_name="unit")
    runtime.start()
    created = runtime.submit_job(
        JobRequest(
            job_type="CREATE_BEING",
            job_id="c0",
            payload={"name": "Crow", "species": "ANIMAL", "archetype": "CROW"},
        )
    )
    being_id = created["result"]["being"]["being_id"]
    sim = runtime.submit_job(
        JobRequest(
            job_type="RUN_CREATURE_SIMULATION",
            job_id="c1",
            payload={"being_id": being_id, "ticks": 15, "seed": 99},
        )
    )
    assert sim["ok"] is True
    assert sim["result"]["llm_used"] is False
    assert len(sim["result"]["trajectory"]) == 15
