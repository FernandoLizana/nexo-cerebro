"""P2 browser integration tests — require Playwright + Chromium."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nexo.core.environment_protocol import action_schemas_for, apply_action_outcome
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig
from nexo_qa.browser import BrowserConfig, BrowserWorld, PlaywrightDriver
from nexo_qa.scenarios.browser_lab import GOAL, TEST_DATA, is_success_url
from nexo_qa.testing import bind_world
from nexo_qa.testing.web_lab_server import WebLabServer

pytestmark = pytest.mark.browser

FORBIDDEN_IN_CORE = (
    "css_selector",
    "xpath",
    "locator",
    "elementhandle",
    "playwright",
    "#",
    "data-testid",
)


def _require_playwright() -> None:
    pytest.importorskip("playwright")


def _lab_config(**overrides) -> BrowserConfig:
    base = BrowserConfig(test_data=dict(TEST_DATA), headless=True)
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


@pytest.fixture
def web_lab_url():
    _require_playwright()
    with WebLabServer() as server:
        yield server.base_url


def test_playwright_driver_smoke(web_lab_url: str) -> None:
    driver = PlaywrightDriver(config=_lab_config())
    try:
        driver.start()
        driver.navigate(web_lab_url)
        snap = driver.snapshot()
        assert snap.url.startswith("http://127.0.0.1")
        assert any(e.visible_text or e.role for e in snap.visible_elements)
        result = driver.execute(
            __import__("nexo_qa.browser.models", fromlist=["BrowserCommand"]).BrowserCommand(
                command_type="CLICK",
                element_id=snap.visible_elements[0].element_id,
            )
        )
        assert result.executed or result.failed  # structured result always
    finally:
        driver.close()


def test_browser_snapshot_visible_elements(web_lab_url: str) -> None:
    driver = PlaywrightDriver(config=_lab_config())
    try:
        driver.start()
        driver.navigate(web_lab_url)
        snap = driver.snapshot()
        texts = " ".join(e.visible_text for e in snap.visible_elements).lower()
        assert "comenzar" in texts or "bienvenido" in texts
        for element in snap.visible_elements:
            assert element.element_id.startswith("web:e:")
            assert "#" not in element.element_id
    finally:
        driver.close()


def test_browserworld_generates_actions_from_visible_state(web_lab_url: str) -> None:
    world = BrowserWorld(initial_url=web_lab_url, config=_lab_config(), goal=GOAL)
    with world:
        schemas = world.action_schemas()
        assert schemas
        labels = [s.label for s in schemas]
        assert any("activate" in lbl.lower() or "comenzar" in lbl.lower() for lbl in labels)
        serialized = json.dumps([s.to_dict() for s in schemas]).lower()
        assert "data-testid" not in serialized
        assert "css_selector" not in serialized


def test_browserworld_executes_selected_action(web_lab_url: str) -> None:
    world = BrowserWorld(initial_url=web_lab_url, config=_lab_config())
    with world:
        action_id = next(
            s.id for s in world.action_schemas() if "comenzar" in s.label.lower() or "activate" in s.label.lower()
        )
        raw, outcome = apply_action_outcome(world, action_id)
        assert outcome.accepted is True
        assert raw.get("url_after", world.driver._page.url if world.driver and world.driver._page else "").endswith(
            ("name.html", "name.html/")
        ) or "name.html" in str(raw.get("url_after", ""))


def test_browserworld_state_transition(web_lab_url: str) -> None:
    world = BrowserWorld(initial_url=web_lab_url, config=_lab_config())
    with world:
        url0 = world.driver.snapshot().url if world.driver else web_lab_url
        start = next(s.id for s in world.action_schemas() if "comenzar" in s.label.lower())
        apply_action_outcome(world, start)
        url1 = world.driver.snapshot().url if world.driver else ""
        assert url1 != url0
        assert world.available_actions() != action_schemas_for(world) or len(world.action_schemas()) > 0


def test_selector_secrecy(web_lab_url: str) -> None:
    world = BrowserWorld(initial_url=web_lab_url, config=_lab_config())
    with world:
        blob = json.dumps([s.to_dict() for s in world.action_schemas()]).lower()
        for token in FORBIDDEN_IN_CORE:
            assert token not in blob


def test_navigation_policy_block(web_lab_url: str) -> None:
    world = BrowserWorld(initial_url=web_lab_url, config=_lab_config())
    with world:
        from nexo_qa.browser.models import BrowserCommand

        result = world.driver.execute(BrowserCommand(command_type="NAVIGATE", url="https://example.com"))
        assert result.failed
        assert result.error_type == "POLICY_BLOCKED"


def test_browser_resource_cleanup(web_lab_url: str) -> None:
    world = BrowserWorld(initial_url=web_lab_url, config=_lab_config())
    world.start()
    assert world.driver._page is not None
    world.close()
    assert world.driver._page is None
    assert world.driver._browser is None


def _integrated_runtime(ticks: int = 48) -> IntegratedRuntime:
    return IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=ticks,
            executive_mode="integrated",
            perception_mode="predictive",
            memory_mode="integrated",
            causal_certificate_mode="integrated",
            agency_audit_mode="integrated",
            profile="p2_browser",
        )
    )


def test_first_autonomous_web_loop(web_lab_url: str) -> None:
    rt = _integrated_runtime(ticks=64)
    world = BrowserWorld(initial_url=web_lab_url, config=_lab_config(), goal=GOAL, seed=42)
    bind_world(rt, world)
    world.start()
    try:
        result = rt.run()
        selected = [
            ev.payload.get("selected_action_id") or ev.payload.get("action")
            for ev in rt.state_store.event_log
            if ev.event_type == "action.selected"
        ]
        assert len(selected) >= 3
        assert len(set(selected)) >= 2
        assert len(world.action_history) >= 2
        urls = {entry["payload"].get("url") for entry in world.trace_log if entry["event_type"] == "BROWSER_SNAPSHOT"}
        assert len(urls) >= 2
        assert result["executive_mode"] == "integrated"
        rewards = [ev for ev in rt.state_store.event_log if ev.event_type == "reward.received"]
        assert rewards
        certs = [ev for ev in rt.state_store.event_log if ev.event_type == "causal.certificate"]
        assert certs
    finally:
        world.close()


def test_browserworld_agency_alternatives_on_plan_page(web_lab_url: str) -> None:
    world = BrowserWorld(initial_url=web_lab_url.replace("index.html", "plan.html?name=Nexo"), config=_lab_config())
    with world:
        labels = [s.label.lower() for s in world.action_schemas()]
        assert any("básico" in lbl or "basico" in lbl for lbl in labels)
        assert any("pro" in lbl for lbl in labels)
        assert len(world.available_actions()) >= 2
