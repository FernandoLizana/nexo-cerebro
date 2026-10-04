"""STOP / cooperative cancel regressions for the local node runtime."""

from __future__ import annotations

from pathlib import Path

import pytest

from services.being.store import BeingStore
from services.creature.engine import run_creature_ticks
from services.node.jobs import JobRejected, JobRequest
from services.node.runtime import NodeRuntime


def test_creature_ticks_cooperative_should_stop(tmp_path: Path) -> None:
    runtime = NodeRuntime(data_dir=tmp_path / "node", node_name="stop-unit")
    runtime.start()
    created = runtime.submit_job(
        JobRequest(
            job_type="CREATE_BEING",
            job_id="stop-create",
            payload={"name": "StopCrow", "species": "ANIMAL", "archetype": "CROW"},
        )
    )
    being_id = created["result"]["being"]["being_id"]
    store = BeingStore(tmp_path / "node" / "beings")
    being = store.load(being_id)
    calls = {"n": 0}

    def should_stop() -> bool:
        calls["n"] += 1
        return calls["n"] > 4

    result = run_creature_ticks(being, ticks=200, seed=3, should_stop=should_stop)
    assert result["stopped"] is True
    assert result["ok"] is False
    assert result["ticks"] == 4
    assert result["ticks"] < result["ticks_requested"]


def test_runtime_stop_mid_sim_skips_success_persist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = NodeRuntime(data_dir=tmp_path / "node", node_name="stop-persist")
    runtime.start()
    created = runtime.submit_job(
        JobRequest(
            job_type="CREATE_BEING",
            job_id="stop-create-2",
            payload={"name": "HaltFox", "species": "ANIMAL", "archetype": "FOX"},
        )
    )
    being_id = created["result"]["being"]["being_id"]
    store = BeingStore(tmp_path / "node" / "beings")
    before = store.load(being_id)
    before_drives = dict(before.state.drives)
    state_bytes = store.paths_for(being_id).state.read_bytes()

    import services.creature.engine as creature_engine

    real_run = creature_engine.run_creature_ticks

    def stop_after_few(being, *, ticks, seed=0, memory=None, should_stop=None):
        n = {"i": 0}

        def flip() -> bool:
            n["i"] += 1
            if n["i"] > 3:
                return True
            return bool(should_stop and should_stop())

        out = real_run(being, ticks=ticks, seed=seed, memory=memory, should_stop=flip)
        # Simulate in-memory learning that must NOT hit disk on cancel.
        being.state.drives["hunger"] = 0.97
        being.state.learned_behavior_notes.append("should-not-persist-on-stop")
        assert out["stopped"] is True
        return out

    monkeypatch.setattr(creature_engine, "run_creature_ticks", stop_after_few)

    with pytest.raises(JobRejected, match="cancelled by stop"):
        runtime.submit_job(
            JobRequest(
                job_type="RUN_CREATURE_SIMULATION",
                job_id="stop-sim",
                payload={"being_id": being_id, "ticks": 500, "seed": 11},
            )
        )

    assert store.paths_for(being_id).state.read_bytes() == state_bytes
    reloaded = store.load(being_id)
    assert reloaded.state.drives == before_drives
    assert "should-not-persist-on-stop" not in reloaded.state.learned_behavior_notes
