"""P1 quality gate: same Cognitive Core on RoomWorld and MockWorld."""

from __future__ import annotations

import ast
from pathlib import Path

from nexo.core.environment_protocol import EnvironmentProtocol, action_schemas_for
from nexo.demo.room_scenario import RoomWorld
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig
from nexo_qa.testing import bind_world
from nexo_qa.testing.mock_world import MockWorld

ROOT = Path(__file__).resolve().parent.parent


def _p1_runtime(**overrides) -> IntegratedRuntime:
    payload = {
        "seed": 42,
        "ticks": 16,
        "executive_mode": "integrated",
        "perception_mode": "predictive",
        "memory_mode": "integrated",
        "causal_certificate_mode": "integrated",
        "agency_audit_mode": "integrated",
        "profile": "p1_two_worlds",
    }
    payload.update(overrides)
    return IntegratedRuntime(IntegratedRuntimeConfig(**payload))


def test_two_worlds_one_brain() -> None:
    room = RoomWorld()
    mock = MockWorld(seed=42)
    assert isinstance(room, EnvironmentProtocol)
    assert isinstance(mock, EnvironmentProtocol)

    rt_room = _p1_runtime()
    room_schemas_start = action_schemas_for(rt_room.world)
    room_result = rt_room.run()
    room_schemas = action_schemas_for(rt_room.world)
    room_selected = [
        ev.payload.get("selected_action_id") or ev.payload.get("action")
        for ev in rt_room.state_store.event_log
        if ev.event_type == "action.selected"
    ]
    room_rewards = [ev for ev in rt_room.state_store.event_log if ev.event_type == "reward.received"]
    room_certs = [ev for ev in rt_room.state_store.event_log if ev.event_type == "causal.certificate"]
    room_agency = [ev for ev in rt_room.state_store.event_log if ev.event_type == "agency.audit"]

    rt_mock = _p1_runtime()
    bind_world(rt_mock, MockWorld(seed=42))
    mock_schemas_start = action_schemas_for(rt_mock.world)
    mock_result = rt_mock.run()
    mock_schemas = action_schemas_for(rt_mock.world)
    mock_selected = [
        ev.payload.get("selected_action_id") or ev.payload.get("action")
        for ev in rt_mock.state_store.event_log
        if ev.event_type == "action.selected"
    ]
    mock_rewards = [ev for ev in rt_mock.state_store.event_log if ev.event_type == "reward.received"]
    mock_certs = [ev for ev in rt_mock.state_store.event_log if ev.event_type == "causal.certificate"]
    mock_agency = [ev for ev in rt_mock.state_store.event_log if ev.event_type == "agency.audit"]

    assert room_result["executive_mode"] == mock_result["executive_mode"] == "integrated"
    assert {s.id for s in room_schemas_start} != {s.id for s in mock_schemas_start}
    assert "eat" in {s.id for s in room_schemas_start}
    assert "inspect_panel" in {s.id for s in mock_schemas_start}
    assert {s.id for s in mock_schemas_start} != {s.id for s in mock_schemas}
    assert all(schema.id in {"eat", "rest", "flee", "approach_caregiver", "explore", "inspect_distractor"} for schema in room_schemas)
    assert room_selected
    assert mock_selected
    assert set(mock_selected) <= {
        "inspect_panel",
        "wait",
        "activate_switch",
        "step_back",
        "collect_target",
        "finish",
    }
    assert "eat" not in mock_selected
    assert room_rewards and mock_rewards
    assert room_certs and mock_certs
    assert room_agency and mock_agency
    assert rt_mock.world.phase in {"armed", "open", "done"}
    assert len(rt_mock.world.action_history) >= 2

    rt_mock_b = _p1_runtime()
    bind_world(rt_mock_b, MockWorld(seed=42))
    mock_b = rt_mock_b.run()
    assert mock_result["trajectory_hash"] == mock_b["trajectory_hash"]

    core_files = [
        ROOT / "nexo" / "prefrontal" / "deliberation.py",
        ROOT / "nexo" / "core" / "process_executive.py",
        ROOT / "nexo" / "core" / "environment_protocol.py",
    ]
    for path in core_files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "isinstance":
                dumped = ast.dump(node)
                assert "RoomWorld" not in dumped
                assert "MockWorld" not in dumped


def test_mock_world_agency_sees_alternatives() -> None:
    rt = _p1_runtime(ticks=8)
    bind_world(rt, MockWorld(seed=42))
    rt.run()
    selected = [ev for ev in rt.state_store.event_log if ev.event_type == "action.selected"]
    assert selected
    payload = selected[0].payload
    candidates = payload.get("candidate_action_ids") or payload.get("candidates")
    assert candidates is not None
    assert len(tuple(candidates)) >= 2
    assert payload.get("selected_action_id") or payload.get("action")
    agency = [ev for ev in rt.state_store.event_log if ev.event_type == "agency.audit"]
    assert agency
    assert float(agency[-1].payload.get("agency_score", 0.0)) >= 0.0
