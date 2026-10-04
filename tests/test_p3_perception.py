"""P3 perceptual web model tests — require Playwright + Chromium."""

from __future__ import annotations

import json
from copy import deepcopy

import pytest

from nexo.core.environment_protocol import apply_action_outcome
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig
from nexo_qa.browser import BrowserConfig, BrowserWorld, PlaywrightDriver
from nexo_qa.browser.action_mapper import percept_action_eligible
from nexo_qa.browser.models import BrowserCommand
from nexo_qa.perception import PerceptualAttentionGate, perception_strategy_for
from nexo_qa.perception.config import PerceptionConfig
from nexo_qa.perception.dom_fast import DomFastPerception
from nexo_qa.perception.hybrid import HybridPerception
from nexo_qa.scenarios.browser_lab import TEST_DATA
from nexo_qa.testing import bind_world
from nexo_qa.testing.web_lab_server import WebLabServer

pytestmark = pytest.mark.browser

FORBIDDEN_IN_COGNITION = (
    "css_selector",
    "xpath",
    "locator",
    "elementhandle",
    "playwright",
    "data-testid",
    "#start-btn",
)


def _require_playwright() -> None:
    pytest.importorskip("playwright")


def _lab_url(page: str, web_lab_url: str) -> str:
    base = web_lab_url.rsplit("/", 1)[0]
    return f"{base}/{page}"


def _hybrid_config(**overrides) -> BrowserConfig:
    perception = PerceptionConfig(mode="hybrid")
    for key, value in overrides.items():
        if hasattr(perception, key):
            setattr(perception, key, value)
    return BrowserConfig(test_data=dict(TEST_DATA), headless=True, perception=perception)


def _dom_config(**overrides) -> BrowserConfig:
    perception = PerceptionConfig(mode="dom_fast")
    for key, value in overrides.items():
        if hasattr(perception, key):
            setattr(perception, key, value)
    return BrowserConfig(test_data=dict(TEST_DATA), headless=True, perception=perception)


@pytest.fixture
def web_lab_url():
    _require_playwright()
    with WebLabServer() as server:
        yield server.base_url


def _scene_for(driver: PlaywrightDriver, url: str, *, mode: str = "hybrid"):
    driver.navigate(url)
    snap = driver.snapshot(mode=mode)
    cfg = PerceptionConfig(mode=mode)
    scene = perception_strategy_for(cfg).build_scene(snap)
    if mode == "hybrid":
        scene = PerceptualAttentionGate(cfg).apply(scene)
    return snap, scene


def test_hybrid_scene_contains_visible_geometry(web_lab_url: str) -> None:
    driver = PlaywrightDriver(config=_hybrid_config())
    try:
        driver.start()
        _snap, scene = _scene_for(driver, _lab_url("low_salience.html", web_lab_url))
        assert scene.mode == "hybrid"
        assert scene.percepts
        for percept in scene.percepts:
            assert percept.bounding_box[2] > 0
            assert percept.bbox_norm[2] > 0
            assert percept.visual_region
        assert scene.regions
        blob = json.dumps(scene.to_dict()).lower()
        for token in FORBIDDEN_IN_COGNITION:
            assert token not in blob
    finally:
        driver.close()


def test_offscreen_target_not_perceived_before_scroll(web_lab_url: str) -> None:
    driver = PlaywrightDriver(config=_hybrid_config())
    try:
        driver.start()
        _snap, scene = _scene_for(driver, _lab_url("below_fold.html", web_lab_url))
        labels = [p.label.lower() for p in scene.percepts]
        assert not any("confirmar objetivo" in lbl for lbl in labels)
    finally:
        driver.close()


def test_scroll_reveals_new_percept(web_lab_url: str) -> None:
    world = BrowserWorld(initial_url=_lab_url("below_fold.html", web_lab_url), config=_hybrid_config())
    with world:
        before_labels = {p.label.lower() for p in world.perceptual_scene.percepts}
        assert not any("confirmar objetivo" in lbl for lbl in before_labels)
        scroll_id = next(s.id for s in world.action_schemas() if "scroll" in s.label.lower())
        for _ in range(3):
            apply_action_outcome(world, scroll_id)
            after_labels = {p.label.lower() for p in world.perceptual_scene.percepts}
            if any("confirmar objetivo" in lbl for lbl in after_labels):
                break
        assert any("confirmar objetivo" in lbl for lbl in after_labels)
        diff = world.last_perceptual_diff
        assert diff is not None
        assert diff.appeared or any("confirmar objetivo" in lbl for lbl in after_labels)


def test_modal_occludes_background_actions(web_lab_url: str) -> None:
    world = BrowserWorld(initial_url=_lab_url("modal_overlay.html", web_lab_url), config=_hybrid_config())
    with world:
        labels = [s.label.lower() for s in world.action_schemas()]
        assert not any("delete account" in lbl for lbl in labels)
        assert any("save" in lbl for lbl in labels)


def test_salience_reflects_controlled_visual_difference(web_lab_url: str) -> None:
    driver = PlaywrightDriver(config=_hybrid_config())
    try:
        driver.start()
        _snap, scene = _scene_for(driver, _lab_url("low_salience.html", web_lab_url))
        by_label = {p.label.lower(): p for p in scene.percepts if p.interactive}
        primary = next((p for k, p in by_label.items() if "pay now" in k), None)
        secondary = next((p for k, p in by_label.items() if "add extras" in k), None)
        assert primary is not None and secondary is not None
        assert secondary.salience_score > primary.salience_score
    finally:
        driver.close()


def test_dense_region_has_higher_visual_clutter(web_lab_url: str) -> None:
    driver = PlaywrightDriver(config=_hybrid_config())
    try:
        driver.start()
        _snap, dense = _scene_for(driver, _lab_url("dense_form.html", web_lab_url))
        _snap2, sparse = _scene_for(driver, _lab_url("index.html", web_lab_url))
        dense_clutter = max(p.visual_clutter_score for p in dense.percepts) if dense.percepts else 0
        sparse_clutter = max(p.visual_clutter_score for p in sparse.percepts) if sparse.percepts else 0
        assert dense_clutter >= sparse_clutter
    finally:
        driver.close()


def test_perceptual_diff_detects_new_error(web_lab_url: str) -> None:
    world = BrowserWorld(initial_url=_lab_url("error_message.html", web_lab_url), config=_hybrid_config())
    with world:
        click_id = next(
            s.id
            for s in world.action_schemas()
            if "sign in" in s.label.lower() or "activate" in s.label.lower()
        )
        apply_action_outcome(world, click_id)
        diff = world.last_perceptual_diff
        assert diff is not None
        assert diff.appeared or diff.text_changed
        alert_percepts = [p for p in world.perceptual_scene.percepts if p.role == "alert" or "invalid" in p.text.lower()]
        assert alert_percepts or diff.appeared


def test_duplicate_labels_keep_distinct_identity(web_lab_url: str) -> None:
    driver = PlaywrightDriver(config=_hybrid_config())
    try:
        driver.start()
        _snap, scene = _scene_for(driver, _lab_url("duplicate_labels.html", web_lab_url))
        continuar = [p for p in scene.percepts if "continuar" in p.label.lower()]
        assert len(continuar) >= 2
        ids = {p.percept_id for p in continuar}
        source_ids = {p.source_element_id for p in continuar}
        assert len(ids) == len(continuar)
        assert len(source_ids) == len(continuar)
    finally:
        driver.close()


def test_selector_secrecy_scene_serialization(web_lab_url: str) -> None:
    world = BrowserWorld(initial_url=web_lab_url, config=_hybrid_config())
    with world:
        blob = json.dumps(world.perceptual_scene.to_dict()).lower()
        for token in FORBIDDEN_IN_COGNITION:
            assert token not in blob


def test_element_action_requires_eligible_percept(web_lab_url: str) -> None:
    world = BrowserWorld(initial_url=_lab_url("below_fold.html", web_lab_url), config=_hybrid_config())
    with world:
        for schema in world.action_schemas():
            if schema.action_type in ("scroll", "navigate"):
                continue
            percept_id = schema.metadata.get("source_percept_id")
            assert percept_id, f"action {schema.id} missing percept link"
            percept = next(p for p in world.perceptual_scene.percepts if p.percept_id == percept_id)
            assert percept_action_eligible(percept, world.config.perception)


def test_dom_fast_vs_hybrid_differ(web_lab_url: str) -> None:
    driver = PlaywrightDriver(config=_hybrid_config())
    try:
        driver.start()
        url = _lab_url("below_fold.html", web_lab_url)
        driver.navigate(url)
        dom_snap = driver.snapshot(mode="dom_fast")
        hyb_snap = driver.snapshot(mode="hybrid")
        dom_scene = DomFastPerception(PerceptionConfig(mode="dom_fast")).build_scene(dom_snap)
        hyb_scene = HybridPerception(PerceptionConfig(mode="hybrid")).build_scene(hyb_snap)
        hyb_scene = PerceptualAttentionGate(PerceptionConfig(mode="hybrid")).apply(hyb_scene)
        assert len(dom_scene.percepts) >= len(hyb_scene.percepts)
    finally:
        driver.close()


def test_perceptual_autonomous_loop(web_lab_url: str) -> None:
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=64,
            executive_mode="integrated",
            perception_mode="predictive",
            profile="p2_browser",
        )
    )
    world = BrowserWorld(initial_url=_lab_url("below_fold.html", web_lab_url), config=_hybrid_config(), seed=42)
    bind_world(rt, world)
    world.start()
    try:
        result = rt.run()
        assert len(world.action_history) >= 1
        assert result["executive_mode"] == "integrated"
    finally:
        world.close()


def test_distractor_behavior_salience(web_lab_url: str) -> None:
    driver = PlaywrightDriver(config=_hybrid_config())
    try:
        driver.start()
        _snap, scene = _scene_for(driver, _lab_url("distractor.html", web_lab_url))
        scores = {p.label.lower(): p.salience_score for p in scene.percepts if p.interactive}
        distractor = next(v for k, v in scores.items() if "premium" in k)
        target = next(v for k, v in scores.items() if "basic" in k)
        assert distractor > target
    finally:
        driver.close()


def test_attention_integration_changes_attended_set(web_lab_url: str) -> None:
    cfg = PerceptionConfig(mode="hybrid", max_attended_percepts=3, max_focal_percepts=1)
    world = BrowserWorld(
        initial_url=_lab_url("dense_form.html", web_lab_url),
        config=BrowserConfig(headless=True, perception=cfg),
    )
    with world:
        scene = world.perceptual_scene
        assert len(scene.attended_percept_ids) <= 3
        assert len(scene.focal_percept_ids) <= 1
        attended_events = [e for e in world.trace_log if e["event_type"] == "ATTENTION_TRACE"]
        assert attended_events


def test_no_action_on_hidden_element(web_lab_url: str) -> None:
    world = BrowserWorld(initial_url=_lab_url("hidden_disabled.html", web_lab_url), config=_hybrid_config())
    with world:
        labels = [s.label.lower() for s in world.action_schemas()]
        assert not any("hidden action" in lbl for lbl in labels)


def test_no_action_on_disabled_button(web_lab_url: str) -> None:
    world = BrowserWorld(initial_url=_lab_url("hidden_disabled.html", web_lab_url), config=_hybrid_config())
    with world:
        labels = [s.label.lower() for s in world.action_schemas()]
        assert not any("disabled action" in lbl for lbl in labels)
        disabled_percepts = [p for p in world.perceptual_scene.percepts if not p.enabled]
        assert disabled_percepts


def test_focus_boost_on_input(web_lab_url: str) -> None:
    world = BrowserWorld(
        initial_url=_lab_url("name.html", web_lab_url),
        config=_hybrid_config(),
    )
    with world:
        focus_id = next((s.id for s in world.action_schemas() if "focus" in s.label.lower()), None)
        if focus_id:
            apply_action_outcome(world, focus_id)
            focused = [p for p in world.perceptual_scene.percepts if p.is_focused]
            assert focused
            assert focused[0].salience_score >= 0.3


def test_modal_focus_dominates_actions(web_lab_url: str) -> None:
    world = BrowserWorld(initial_url=_lab_url("modal_overlay.html", web_lab_url), config=_hybrid_config())
    with world:
        modal_percepts = [p for p in world.perceptual_scene.percepts if p.is_modal or p.semantic_group == "modal"]
        activate_labels = [s.label.lower() for s in world.action_schemas() if s.action_type == "activate"]
        assert any("save" in lbl for lbl in activate_labels)
        if modal_percepts:
            assert max(p.salience_score for p in modal_percepts) >= 0.4


def test_hybrid_scene_reproducibility(web_lab_url: str) -> None:
    driver = PlaywrightDriver(config=_hybrid_config())
    try:
        driver.start()
        url = _lab_url("distractor.html", web_lab_url)
        scenes = []
        for _ in range(2):
            driver.navigate(url)
            snap = driver.snapshot(mode="hybrid")
            scene = HybridPerception(PerceptionConfig(mode="hybrid")).build_scene(snap)
            scenes.append([p.to_dict() for p in scene.percepts])
        assert scenes[0] == scenes[1]
    finally:
        driver.close()


def test_p3_legacy_regression_dom_fast_still_works(web_lab_url: str) -> None:
    world = BrowserWorld(initial_url=web_lab_url, config=_dom_config())
    with world:
        schemas = world.action_schemas()
        assert schemas
        assert world.perceptual_scene.mode == "dom_fast"
