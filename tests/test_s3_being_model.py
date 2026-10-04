"""S3 — Being model / Character Creator tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from services.being.creator import being_public_summary, create_being
from services.being.models import (
    EXPERIMENTAL_DISCLAIMER,
    PERSONALITY_TRAITS,
    BeingArchetype,
    BeingSpecies,
)
from services.being.store import BeingStore
from services.being.validation import BeingValidationError


def test_create_and_reload_split_store(tmp_path: Path) -> None:
    store = BeingStore(tmp_path / "beings")
    being = create_being(
        name="Nira",
        species=BeingSpecies.HUMANOID,
        archetype=BeingArchetype.EXPLORER,
        creator_node="nexo-node-test",
        traits={"curiosity": 0.9, "caution": 0.2},
        interests=["maps"],
        goals=["explore"],
        store=store,
    )
    paths = store.paths_for(being.identity.being_id)
    assert paths.identity.is_file()
    assert paths.memory_index.is_file()
    assert paths.state.is_file()
    assert paths.cognitive.is_file()
    assert not (paths.root / "being.json").exists()

    loaded = store.load(being.identity.being_id)
    assert loaded.identity.name == "Nira"
    assert loaded.identity.core_personality.traits["curiosity"] == pytest.approx(0.9)
    assert loaded.identity.core_personality.disclaimer == EXPERIMENTAL_DISCLAIMER
    assert "PRIVATE" not in str(being_public_summary(loaded))


def test_personality_bounds_and_unknown_trait(tmp_path: Path) -> None:
    store = BeingStore(tmp_path / "beings")
    with pytest.raises(BeingValidationError, match="unknown personality"):
        create_being(
            name="Bad",
            species="HUMANOID",
            creator_node="node-a",
            traits={"love_real": 1.0},
            store=store,
        )
    with pytest.raises(BeingValidationError):
        create_being(
            name="Bad2",
            species="HUMANOID",
            creator_node="node-a",
            traits={"curiosity": 1.5},
            store=store,
        )


def test_animal_defaults_without_llm(tmp_path: Path) -> None:
    store = BeingStore(tmp_path / "beings")
    dog = create_being(
        name="Bolt",
        species=BeingSpecies.ANIMAL,
        archetype=BeingArchetype.DOG,
        creator_node="node-a",
        store=store,
    )
    assert dog.cognitive.use_llm is False
    assert "hunger" in dog.state.drives
    assert dog.identity.core_personality.traits["sociability"] >= 0.5
    assert set(PERSONALITY_TRAITS) <= set(dog.identity.core_personality.traits)


def test_list_beings(tmp_path: Path) -> None:
    store = BeingStore(tmp_path / "beings")
    a = create_being(name="A", species="CREATURE", archetype="SLIME", creator_node="n", store=store)
    b = create_being(name="B", species="EXPERIMENTAL", creator_node="n", store=store)
    ids = store.list_ids()
    assert a.identity.being_id in ids
    assert b.identity.being_id in ids


def test_node_create_being_job(tmp_path: Path) -> None:
    from services.node.jobs import JobRequest
    from services.node.runtime import NodeRuntime

    runtime = NodeRuntime(data_dir=tmp_path / "node", node_name="unit")
    runtime.start()
    result = runtime.submit_job(
        JobRequest(
            job_type="CREATE_BEING",
            job_id="b1",
            payload={"name": "Foxie", "species": "ANIMAL", "archetype": "FOX"},
        )
    )
    assert result["ok"] is True
    assert result["result"]["created"] is True
    assert "disclaimer" in result["result"]["being"]
    listed = runtime.submit_job(JobRequest(job_type="LIST_BEINGS", job_id="b2"))
    assert result["result"]["being"]["being_id"] in listed["result"]["beings"]
