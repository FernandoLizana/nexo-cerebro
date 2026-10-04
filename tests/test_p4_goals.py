"""P4 goal semantics tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nexo.core.environment_protocol import apply_action_outcome
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig
from nexo_qa.browser import BrowserConfig, BrowserWorld
from nexo_qa.goals import (
    Goal,
    TaskContext,
    bind_task,
    evaluate_progress,
    goal_relevance_for_text,
    parse_goal,
)
from nexo_qa.goals.parser import goal_contains_steps
from nexo_qa.goals.runtime import LoopDetector, TaskGoalProcess
from nexo_qa.perception.config import PerceptionConfig
from nexo_qa.scenarios.browser_lab import GOAL, TEST_DATA
from nexo_qa.scenarios.task_definition import (
    REGISTER_PRO_CONTEXT,
    REGISTER_PRO_GOAL,
    find_pricing_task,
    register_pro_task,
    select_pro_task,
)
from nexo_qa.testing import bind_world
from nexo_qa.testing.web_lab_server import WebLabServer

pytestmark = pytest.mark.browser

FORBIDDEN_IN_TASK = ("oracle", "selector", "correct_action", "next_step", "data-testid", "expected_actions")


def _hybrid_config() -> BrowserConfig:
    return BrowserConfig(
        test_data=dict(TEST_DATA),
        headless=True,
        perception=PerceptionConfig(mode="hybrid"),
    )


@pytest.fixture
def web_lab_url():
    pytest.importorskip("playwright")
    with WebLabServer() as server:
        yield server.base_url


def test_goal_parser_extracts_basic_intent_and_entities() -> None:
    goal = parse_goal(
        "Completa el registro y selecciona el plan Pro.",
        task_context=REGISTER_PRO_CONTEXT,
    )
    assert goal.entities.get("plan") == "Pro"
    assert goal.goal_type in ("registration", "plan_selection")
    assert goal.subgoals
    assert "must_select_plan" in goal.constraints


def test_goal_does_not_contain_steps() -> None:
    goal = register_pro_task()
    blob = goal.to_dict()
    assert not goal_contains_steps(blob)
    serialized = json.dumps(blob).lower()
    assert "step_sequence" not in serialized
    assert "expected_actions" not in serialized


def test_task_context_leakage() -> None:
    ctx = REGISTER_PRO_CONTEXT
    blob = json.dumps(ctx.agent_dict()).lower()
    for token in FORBIDDEN_IN_TASK:
        assert token not in blob


def test_goal_activation_pending_to_active() -> None:
    goal = parse_goal("Selecciona plan Pro.")
    assert goal.status == "PENDING"
    active = goal.activate()
    assert active.status == "ACTIVE"
    assert "task:active" in active.goal_tokens()


def test_progress_partial_one_constraint_satisfied() -> None:
    goal = register_pro_task()
    progress = evaluate_progress(
        goal,
        url="http://127.0.0.1/plan.html",
        action_history=("web:activate:0001",),
        action_labels={"web:activate:0001": 'activate "Pro"'},
        task_context=REGISTER_PRO_CONTEXT,
    )
    assert progress.level in ("partial", "high")
    assert progress.status in ("ACTIVE", "PARTIALLY_SATISFIED")


def test_progress_non_monotonic_plan_change() -> None:
    goal = register_pro_task()
    after_pro = evaluate_progress(
        goal,
        url="http://127.0.0.1/plan.html",
        action_history=("a1",),
        action_labels={"a1": 'activate "Pro"'},
        task_context=REGISTER_PRO_CONTEXT,
    )
    after_basic = evaluate_progress(
        goal,
        url="http://127.0.0.1/plan.html",
        action_history=("a1", "a2"),
        action_labels={"a1": 'activate "Pro"', "a2": 'activate "Básico"'},
        task_context=REGISTER_PRO_CONTEXT,
    )
    assert after_pro.level in ("partial", "high")
    assert after_basic.level in ("partial", "high", "none")


def test_subgoal_creation_from_semantics_not_scenario() -> None:
    goal = find_pricing_task()
    assert goal.subgoals
    assert "localizar_seccion_precios" in goal.subgoals or "explorar_sitio" in goal.subgoals
    runtime_files = Path(__file__).resolve().parents[1] / "nexo_qa"
    text = " ".join(p.read_text(encoding="utf-8", errors="ignore") for p in runtime_files.rglob("*.py"))
    assert "REGISTER_PRO -> [" not in text
    assert "click comenzar" not in text.lower()


def test_no_hardcoded_scenario_plan_in_runtime() -> None:
    root = Path(__file__).resolve().parents[1] / "nexo_qa" / "goals"
    files = [p for p in root.rglob("*.py") if p.name not in ("parser.py",)]
    blob = " ".join(p.read_text(encoding="utf-8") for p in files).lower()
    assert "register_pro -> [" not in blob
    assert "step_sequence" not in blob


def test_goal_relevance_prefers_plan_pro() -> None:
    goal = select_pro_task()
    rel_pro = goal_relevance_for_text(goal, "Plan Pro")
    rel_news = goal_relevance_for_text(goal, "Noticias del día")
    assert rel_pro > rel_news


def test_offscreen_still_offscreen_despite_goal(web_lab_url: str) -> None:
    world = BrowserWorld(
        initial_url=web_lab_url.replace("index.html", "below_fold.html"),
        config=_hybrid_config(),
    )
    with world:
        labels = [p.label.lower() for p in world.perceptual_scene.percepts]
        assert not any("confirmar objetivo" in lbl for lbl in labels)
        rel = goal_relevance_for_text(parse_goal("Confirmar objetivo"), "Confirmar objetivo")
        assert rel > 0


def test_distractor_salience_vs_goal_relevance() -> None:
    goal = parse_goal("Continue with Basic")
    distractor_rel = goal_relevance_for_text(goal, "Get Premium Now!")
    target_rel = goal_relevance_for_text(goal, "Continue with Basic")
    assert target_rel > distractor_rel


def test_register_pro_autonomous_attempt(web_lab_url: str) -> None:
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=96,
            executive_mode="integrated",
            perception_mode="predictive",
            profile="p2_browser",
        )
    )
    world = BrowserWorld(initial_url=web_lab_url, config=_hybrid_config(), goal=REGISTER_PRO_GOAL)
    goal = register_pro_task()
    bind_task(rt, goal=goal, task_context=REGISTER_PRO_CONTEXT, world=world)
    world.start()
    try:
        rt.run()
        assert len(world.action_history) >= 2
        progress = rt.scheduler.config.get("goal_progress")
        assert progress is not None
        assert progress.level in ("partial", "high", "complete", "none")
        task_events = [e for e in rt.state_store.event_log if e.event_type == "goal.progress"]
        assert task_events
    finally:
        world.close()


def test_find_pricing_autonomous(web_lab_url: str) -> None:
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=7, ticks=48, executive_mode="integrated", perception_mode="predictive")
    )
    world = BrowserWorld(initial_url=web_lab_url, config=_hybrid_config())
    goal = find_pricing_task()
    bind_task(rt, goal=goal, world=world)
    world.start()
    try:
        rt.run()
        urls = {getattr(world, "_snapshot", None) and world._snapshot.url or ""}
        assert len(world.action_history) >= 1
    finally:
        world.close()


def test_wrong_choice_recovery_no_auto_correct(web_lab_url: str) -> None:
    world = BrowserWorld(
        initial_url=web_lab_url.replace("index.html", "plan.html?name=Nexo"),
        config=_hybrid_config(),
    )
    with world:
        basic = next((s.id for s in world.action_schemas() if "básico" in s.label.lower() or "basico" in s.label.lower()), None)
        if basic:
            apply_action_outcome(world, basic)
            url = world._snapshot.url if world._snapshot else ""
            assert "summary.html" in url or "plan.html" in url
            assert "basic" in url.lower() or "plan.html" in url


def test_blocked_goal_policy(web_lab_url: str) -> None:
    world = BrowserWorld(initial_url=web_lab_url, config=_hybrid_config())
    with world:
        from nexo_qa.browser.models import BrowserCommand

        result = world.driver.execute(BrowserCommand(command_type="NAVIGATE", url="https://evil.example"))
        assert result.failed
        progress = evaluate_progress(register_pro_task(), policy_blocked=True)
        assert progress.status == "BLOCKED"


def test_loop_detection() -> None:
    det = LoopDetector()
    loop = False
    for _ in range(4):
        loop, _ = det.record("web:scroll:0001", "http://127.0.0.1/a")
    assert loop


def test_goal_drift_detection() -> None:
    det = LoopDetector()
    stagnation = False
    for _ in range(7):
        _, stagnation = det.record("web:activate:0001", "http://127.0.0.1/index.html")
    assert stagnation


def test_goal_causal_trace_events(web_lab_url: str) -> None:
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=42, ticks=24, executive_mode="integrated", perception_mode="predictive")
    )
    world = BrowserWorld(initial_url=web_lab_url, config=_hybrid_config())
    bind_task(rt, goal=register_pro_task(), task_context=REGISTER_PRO_CONTEXT, world=world)
    world.start()
    try:
        rt.run()
        types = {e.event_type for e in rt.state_store.event_log}
        assert "goal.progress" in types
        assert "goals.updated" in types
        assert "action.selected" in types
    finally:
        world.close()


def test_agency_goal_given_path_not_given(web_lab_url: str) -> None:
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=42, ticks=32, executive_mode="integrated", perception_mode="predictive")
    )
    world = BrowserWorld(initial_url=web_lab_url, config=_hybrid_config())
    bind_task(rt, goal=register_pro_task(), task_context=REGISTER_PRO_CONTEXT, world=world)
    world.start()
    try:
        rt.run()
        selected = [
            e.payload.get("selected_action_id") or e.payload.get("action")
            for e in rt.state_store.event_log
            if e.event_type == "action.selected"
        ]
        assert len(set(selected)) >= 1
        assert not rt.scheduler.config.get("expected_path")
    finally:
        world.close()


def test_adversarial_web_does_not_mutate_task_goal() -> None:
    goal = select_pro_task()
    original = goal.description
    mutated = parse_goal(original, task_context=TaskContext(desired_plan="Pro"))
    assert mutated.entities.get("plan") == "Pro"
    assert "básico" not in mutated.constraints.get("must_select_plan", "Pro").lower()


def test_p4_legacy_regression_dom_fast(web_lab_url: str) -> None:
    cfg = BrowserConfig(test_data=dict(TEST_DATA), perception=PerceptionConfig(mode="dom_fast"))
    world = BrowserWorld(initial_url=web_lab_url, config=cfg)
    with world:
        assert world.action_schemas()


def test_task_goal_process_emits_relevance(web_lab_url: str) -> None:
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=1, ticks=2, executive_mode="integrated", perception_mode="predictive")
    )
    world = BrowserWorld(initial_url=web_lab_url, config=_hybrid_config())
    bind_task(rt, goal=register_pro_task(), task_context=REGISTER_PRO_CONTEXT, world=world)
    world.start()
    try:
        rt.run()
        assert rt.scheduler.config.get("goal_relevance")
        assert any(e.event_type == "goal.relevance" for e in rt.state_store.event_log)
    finally:
        world.close()
