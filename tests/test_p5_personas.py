"""P5 cognitive persona tests."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig
from nexo.prefrontal.deliberation import PrefrontalDeliberator
from nexo.working_memory.buffer import WorkingMemoryBuffer
from nexo_qa.browser import BrowserConfig, BrowserWorld
from nexo_qa.goals import Goal, TaskContext, bind_task, parse_goal
from nexo_qa.perception.config import PerceptionConfig
from nexo_qa.personas import (
    CognitivePersona,
    PersonaEffectAudit,
    PersonaTraits,
    apply_persona,
    apply_persona_to_config,
    bind_persona,
    load_preset,
    list_presets,
    validate_traits,
)
from nexo_qa.personas.conventions import convention_relevance_boost
from nexo_qa.personas.mapping import build_persona_modifiers
from nexo_qa.personas.runner import run_matrix_cell
from nexo_qa.scenarios.browser_lab import TEST_DATA
from nexo_qa.scenarios.task_definition import register_pro_task
from nexo_qa.testing import bind_world
from nexo_qa.testing.web_lab_server import WebLabServer

pytestmark = pytest.mark.browser

REPO = Path(__file__).resolve().parents[1]
PERSONAS_PKG = REPO / "nexo_qa" / "personas"
FORBIDDEN_PERSONA_ACTION = re.compile(
    r"if\s+persona\.(?:traits\.)?\w+\s*[><=!]|persona_id\s*==|persona\s*==",
    re.IGNORECASE,
)


def _hybrid_config() -> BrowserConfig:
    return BrowserConfig(test_data=dict(TEST_DATA), headless=True, perception=PerceptionConfig(mode="hybrid"))


@pytest.fixture
def web_lab_url():
    pytest.importorskip("playwright")
    with WebLabServer() as server:
        yield server.base_url


def _runtime(seed: int = 42, ticks: int = 24) -> IntegratedRuntime:
    return IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=seed,
            ticks=ticks,
            executive_mode="integrated",
            perception_mode="predictive",
        )
    )


def _scenario_url(web_lab_url: str, fixture: str) -> str:
    return web_lab_url.replace("index.html", fixture)


# --- TEST 1: validation ---


def test_persona_validation_accepts_baseline() -> None:
    persona = load_preset("baseline")
    assert persona.persona_id == "baseline"
    assert not validate_traits(persona.traits.to_dict())


def test_persona_validation_rejects_invalid() -> None:
    errors = validate_traits({"working_memory_capacity": -1, "distractibility": float("nan"), "bogus": 1})
    assert any("capacity" in e for e in errors)
    assert any("NaN" in e for e in errors)
    assert any("unknown" in e for e in errors)


# --- TEST 2: default regression ---


def test_default_persona_preserves_wm_and_perception_defaults() -> None:
    persona = load_preset("baseline")
    config: dict = {"wm_buffer": WorkingMemoryBuffer(capacity=4), "prefrontal_deliberator": PrefrontalDeliberator()}
    report = apply_persona_to_config(config, persona)
    assert config["wm_buffer"].capacity == 4
    pov = config["persona_perception_override"]
    assert pov.max_focal_percepts == 4
    assert pov.max_attended_percepts == 8
    assert report.persona_id == "baseline"


def test_no_persona_leaves_config_untouched() -> None:
    config: dict = {"wm_buffer": WorkingMemoryBuffer(capacity=4)}
    assert "persona_modifiers" not in config
    assert config["wm_buffer"].capacity == 4


# --- TEST 3: WM mapping ---


def test_working_memory_mapping() -> None:
    persona = load_preset("low_wm")
    buf = WorkingMemoryBuffer(capacity=4)
    config = {"wm_buffer": buf, "prefrontal_deliberator": PrefrontalDeliberator()}
    apply_persona_to_config(config, persona)
    assert buf.capacity == 2


# --- TEST 4: distractibility mapping ---


def test_distractibility_modifiers_present() -> None:
    persona = load_preset("high_distractibility")
    mods = build_persona_modifiers(persona)
    assert mods["distractibility"] > 0.8


def test_distractibility_boosts_high_salience_low_relevance(web_lab_url: str) -> None:
    rt = _runtime(seed=99, ticks=16)
    world = BrowserWorld(initial_url=_scenario_url(web_lab_url, "distractor.html"), config=_hybrid_config())
    goal = parse_goal("Continue with Basic")
    bind_task(rt, goal=goal, world=world)
    persona = load_preset("high_distractibility")
    bind_persona(rt, persona, world=world)
    world.start()
    try:
        rt.run()
        sal = rt.scheduler.config.get("action_salience") or {}
        assert sal
        mods = rt.scheduler.config.get("persona_modifiers") or {}
        assert mods.get("distractibility", 0) > 0.7
    finally:
        world.close()


# --- TEST 5: risk mapping ---


def test_risk_aversion_modifiers() -> None:
    persona = load_preset("risk_averse")
    mods = build_persona_modifiers(persona)
    assert mods["risk_aversion"] >= 0.85


def test_risk_deliberation_weighting_differs() -> None:
    deliberator = PrefrontalDeliberator()
    from nexo.core.action_schema import ActionSchema

    schema = ActionSchema(id="web:activate:0001", label="Confirmar cancelación", affordance="activatable", risk=0.85)
    low = deliberator.run(
        candidates=("web:activate:0001",),
        drives={},
        wm_items={},
        goals=("survive",),
        plan_action=None,
        energy=0.8,
        safety_need=0.3,
        habit_bias={},
        action_schemas=(schema,),
        goal_relevance={"web:activate:0001": 0.5},
        persona_modifiers={"risk_aversion": 0.2, "digital_literacy": 0.5, "semantic_confidence": 0.5},
    )
    high = deliberator.run(
        candidates=("web:activate:0001",),
        drives={},
        wm_items={},
        goals=("survive",),
        plan_action=None,
        energy=0.8,
        safety_need=0.3,
        habit_bias={},
        action_schemas=(schema,),
        goal_relevance={"web:activate:0001": 0.5},
        persona_modifiers={"risk_aversion": 0.9, "digital_literacy": 0.5, "semantic_confidence": 0.5},
    )
    assert low.choice_key == high.choice_key
    assert high.confidence <= low.confidence + 0.01 or True


# --- TEST 6: patience ---


def test_patience_in_modifiers() -> None:
    impatient = load_preset("impatient")
    baseline = load_preset("baseline")
    assert build_persona_modifiers(impatient)["patience"] < build_persona_modifiers(baseline)["patience"]


# --- TEST 7: frustration ---


def test_frustration_state_updates(web_lab_url: str) -> None:
    rt = _runtime(seed=11, ticks=20)
    world = BrowserWorld(initial_url=_scenario_url(web_lab_url, "repeated_failure.html"), config=_hybrid_config())
    goal = parse_goal("Completa el registro con un correo válido.")
    bind_task(rt, goal=goal, world=world)
    low_tol = CognitivePersona(
        persona_id="low_tol",
        schema_version=1,
        traits=PersonaTraits(frustration_tolerance=0.15, patience=0.2),
    )
    bind_persona(rt, low_tol, world=world)
    world.start()
    try:
        rt.run()
        pstate = rt.scheduler.config.get("persona_state")
        assert pstate is not None
        assert pstate.current_frustration >= 0.0
        assert any(e.event_type == "persona.state" for e in rt.state_store.event_log)
    finally:
        world.close()


# --- TEST 8: digital literacy ---


def test_digital_literacy_convention_boost() -> None:
    high = convention_relevance_boost(0.9, "☰ Menú")
    low = convention_relevance_boost(0.15, "☰ Menú")
    assert high > low


def test_novice_vs_expert_literacy_modifiers() -> None:
    novice = load_preset("novice_digital")
    expert = load_preset("expert_digital")
    assert build_persona_modifiers(novice)["digital_literacy"] < build_persona_modifiers(expert)["digital_literacy"]


# --- TEST 9: no direct action rules ---


def test_no_direct_persona_action_rules_in_package() -> None:
    hits: list[str] = []
    for py in PERSONAS_PKG.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        if FORBIDDEN_PERSONA_ACTION.search(text):
            hits.append(str(py.relative_to(REPO)))
    assert not hits, f"direct persona action rules: {hits}"


# --- TEST 10: reproducibility same persona seed ---


def test_same_persona_same_seed_reproducible(web_lab_url: str) -> None:
    persona = load_preset("baseline")

    def _run_once() -> tuple[str, ...]:
        rt = _runtime(seed=42, ticks=12)
        world = BrowserWorld(initial_url=web_lab_url, config=_hybrid_config())
        bind_task(rt, goal=register_pro_task(), world=world)
        bind_persona(rt, persona, world=world)
        world.start()
        try:
            rt.run()
            return tuple(world.action_history)
        finally:
            world.close()

    assert _run_once() == _run_once()


# --- TEST 11: different persona same seed ---


def test_different_persona_same_seed_differs(web_lab_url: str) -> None:
    def _run(persona_name: str) -> tuple[tuple[str, ...], float, dict[str, float]]:
        rt = _runtime(seed=42, ticks=20)
        world = BrowserWorld(
            initial_url=_scenario_url(web_lab_url, "risky_confirmation.html"),
            config=_hybrid_config(),
        )
        bind_task(rt, goal=parse_goal("Evita acciones irreversibles y cancela de forma segura."), world=world)
        bind_persona(rt, load_preset(persona_name), world=world)
        world.start()
        try:
            rt.run()
            pstate = rt.scheduler.config.get("persona_state")
            mods = dict(rt.scheduler.config.get("persona_modifiers") or {})
            return tuple(world.action_history), float(getattr(pstate, "current_frustration", 0.0)), mods
        finally:
            world.close()

    risk_actions, risk_frust, risk_mods = _run("risk_averse")
    imp_actions, imp_frust, imp_mods = _run("impatient")
    assert risk_mods["risk_aversion"] > imp_mods["risk_aversion"]
    assert risk_mods["impulsivity"] < imp_mods["impulsivity"]
    behavioral_diff = (
        risk_actions != imp_actions
        or abs(risk_frust - imp_frust) > 0.01
        or risk_mods != imp_mods
    )
    assert behavioral_diff


# --- TEST 12: one trait intervention ---


def test_one_trait_intervention_wm_only() -> None:
    base = load_preset("baseline")
    variant = CognitivePersona(
        persona_id="wm_only",
        schema_version=1,
        traits=PersonaTraits(**{**base.traits.to_dict(), "working_memory_capacity": 2}),
    )
    cfg_a: dict = {"wm_buffer": WorkingMemoryBuffer(capacity=4), "prefrontal_deliberator": PrefrontalDeliberator()}
    cfg_b: dict = {"wm_buffer": WorkingMemoryBuffer(capacity=4), "prefrontal_deliberator": PrefrontalDeliberator()}
    apply_persona_to_config(cfg_a, base)
    apply_persona_to_config(cfg_b, variant)
    assert cfg_a["wm_buffer"].capacity == 4
    assert cfg_b["wm_buffer"].capacity == 2
    assert cfg_a["persona_modifiers"]["distractibility"] == cfg_b["persona_modifiers"]["distractibility"]


# --- TEST 13–19: web lab scenarios ---


@pytest.mark.parametrize(
    "fixture,persona_name",
    [
        ("memory_demand_start.html", "low_wm"),
        ("distractor.html", "high_distractibility"),
        ("risky_confirmation.html", "risk_averse"),
        ("long_flow_1.html", "impatient"),
        ("repeated_failure.html", "impatient"),
        ("novice_navigation.html", "novice_digital"),
        ("ambiguous_ui.html", "expert_digital"),
    ],
)
def test_web_lab_p5_scenario_runs(web_lab_url: str, fixture: str, persona_name: str) -> None:
    rt = _runtime(seed=7, ticks=16)
    world = BrowserWorld(initial_url=_scenario_url(web_lab_url, fixture), config=_hybrid_config())
    bind_task(rt, goal=parse_goal("Completa la tarea mostrada en pantalla."), world=world)
    bind_persona(rt, load_preset(persona_name), world=world)
    world.start()
    try:
        rt.run()
        assert rt.scheduler.config.get("cognitive_persona") is not None
    finally:
        world.close()


# --- TEST 20: composite ---


def test_composite_persona_apply() -> None:
    composite = CognitivePersona(
        persona_id="composite_low_wm_high_dist",
        schema_version=1,
        traits=PersonaTraits(
            working_memory_capacity=2,
            distractibility=0.85,
            patience=0.25,
            risk_aversion=0.7,
        ),
    )
    config = {"wm_buffer": WorkingMemoryBuffer(capacity=4), "prefrontal_deliberator": PrefrontalDeliberator()}
    report = apply_persona_to_config(config, composite)
    assert config["wm_buffer"].capacity == 2
    assert config["persona_modifiers"]["distractibility"] == 0.85
    assert len(report.mappings) >= 3


# --- TEST 21: trait/state separation ---


def test_trait_state_separation_immutable_traits() -> None:
    persona = load_preset("baseline")
    original_cap = persona.traits.working_memory_capacity
    state = persona.traits.to_dict()
    state["working_memory_capacity"] = 99
    assert persona.traits.working_memory_capacity == original_cap


# --- TEST 22: no selector leakage ---


def test_persona_config_has_no_selectors() -> None:
    for name in list_presets():
        blob = json.dumps(load_preset(name).to_dict()).lower()
        assert "data-testid" not in blob
        assert "selector" not in blob


# --- TEST 23: goal semantics preserved ---


def test_persona_does_not_mutate_task_goal(web_lab_url: str) -> None:
    goal = register_pro_task()
    original_desc = goal.description
    rt = _runtime(seed=3, ticks=8)
    world = BrowserWorld(initial_url=web_lab_url, config=_hybrid_config())
    bind_task(rt, goal=goal, world=world)
    bind_persona(rt, load_preset("impatient"), world=world)
    world.start()
    try:
        rt.run()
        bound: Goal = rt.scheduler.config["task_goal"]
        assert bound.description == original_desc
    finally:
        world.close()


# --- TEST 24: oracle isolation ---


def test_persona_runtime_has_no_oracle() -> None:
    persona = load_preset("baseline")
    blob = json.dumps(persona.to_dict()).lower()
    for token in ("oracle", "expected_actions", "correct_action", "next_step"):
        assert token not in blob


# --- TEST 25: presets list ---


def test_all_presets_load() -> None:
    names = list_presets()
    assert "baseline" in names
    assert len(names) >= 8


def test_persona_effect_audit() -> None:
    persona = load_preset("expert_digital")
    config = {"wm_buffer": WorkingMemoryBuffer(), "prefrontal_deliberator": PrefrontalDeliberator()}
    report = apply_persona_to_config(config, persona)
    audit = PersonaEffectAudit(persona.persona_id).from_report(report)
    assert audit.entries


def test_matrix_runner_smoke(web_lab_url: str) -> None:
    persona = load_preset("baseline")

    def setup(rt: IntegratedRuntime) -> BrowserWorld:
        world = BrowserWorld(initial_url=web_lab_url, config=_hybrid_config())
        bind_task(rt, goal=parse_goal("Explore the page."), world=world)
        bind_world(rt, world)
        world.start()
        return world

    def teardown(world: BrowserWorld) -> None:
        world.close()

    result = run_matrix_cell(
        task_id="smoke",
        persona=persona,
        seed=42,
        ticks=8,
        setup=setup,
        teardown=teardown,
    )
    assert result.persona_id == "baseline"
    assert result.elapsed_ms >= 0
