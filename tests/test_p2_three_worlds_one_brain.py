"""P2 quality gate: Legacy + Mock + Browser through same Cognitive Core."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from nexo.core.environment_protocol import EnvironmentProtocol, action_schemas_for
from nexo.demo.room_scenario import RoomWorld
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig
from nexo_qa.browser import BrowserConfig, BrowserWorld
from nexo_qa.scenarios.browser_lab import GOAL, TEST_DATA
from nexo_qa.testing import bind_world
from nexo_qa.testing.mock_world import MockWorld
from nexo_qa.testing.web_lab_server import WebLabServer

ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.browser


def _core_runtime(**overrides) -> IntegratedRuntime:
    payload = {
        "seed": 42,
        "ticks": 12,
        "executive_mode": "integrated",
        "perception_mode": "predictive",
        "memory_mode": "integrated",
        "causal_certificate_mode": "integrated",
        "agency_audit_mode": "integrated",
        "profile": "p2_three_worlds",
    }
    payload.update(overrides)
    return IntegratedRuntime(IntegratedRuntimeConfig(**payload))


def test_three_worlds_one_brain() -> None:
    pytest.importorskip("playwright")

    room = RoomWorld()
    mock = MockWorld(seed=42)
    assert isinstance(room, EnvironmentProtocol)
    assert isinstance(mock, EnvironmentProtocol)

    with WebLabServer() as lab:
        browser = BrowserWorld(
            initial_url=lab.base_url,
            config=BrowserConfig(test_data=dict(TEST_DATA), headless=True),
            goal=GOAL,
        )
        assert isinstance(browser, EnvironmentProtocol)

        rt_room = _core_runtime()
        room_ids = {s.id for s in action_schemas_for(rt_room.world)}
        rt_room.run()
        assert "eat" in room_ids

        rt_mock = _core_runtime()
        bind_world(rt_mock, MockWorld(seed=42))
        mock_ids = {s.id for s in action_schemas_for(rt_mock.world)}
        rt_mock.run()
        assert "inspect_panel" in mock_ids

        rt_browser = _core_runtime(ticks=24)
        bind_world(rt_browser, browser)
        browser.start()
        try:
            browser_ids = {s.id for s in action_schemas_for(rt_browser.world)}
            rt_browser.run()
            assert browser_ids
            assert all(i.startswith("web:") for i in browser_ids)
            assert room_ids != mock_ids != browser_ids
            selected = [
                ev.payload.get("action")
                for ev in rt_browser.state_store.event_log
                if ev.event_type == "action.selected"
            ]
            assert selected
        finally:
            browser.close()

    core_files = [
        ROOT / "nexo" / "prefrontal" / "deliberation.py",
        ROOT / "nexo" / "core" / "process_executive.py",
    ]
    for path in core_files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "isinstance":
                dumped = ast.dump(node)
                assert "RoomWorld" not in dumped
                assert "MockWorld" not in dumped
                assert "BrowserWorld" not in dumped
