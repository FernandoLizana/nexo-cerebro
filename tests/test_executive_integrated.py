"""Tests Sprint 5 — PFC, ganglios basales, cerebelo y planificación."""

from __future__ import annotations

from nexo.basal_ganglia.gate import ActionGate
from nexo.cerebellum.coordinator import CerebellarCoordinator
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config
from nexo.planning.goal_stack import GoalStack
from nexo.prefrontal.deliberation import PrefrontalDeliberator
from nexo.random_streams import RandomStreams


def test_pfc_veto_inhibits_distractor_when_low_energy():
    d = PrefrontalDeliberator()
    result = d.run(
        candidates=("eat", "inspect_distractor", "rest"),
        drives={"hunger": 0.55, "curiosity": 0.75, "rest": 0.15},
        wm_items={"eat": 0.5},
        goals=("survive",),
        plan_action=None,
        energy=0.25,
        safety_need=0.2,
        habit_bias={},
    )
    assert result.pfc_veto is True
    assert result.choice_key == "eat"


def test_action_gate_builds_habit():
    gate = ActionGate()
    rng = RandomStreams.from_root_seed(3).decision
    deliberation = None
    from nexo.prefrontal.contestant import DeliberationResult

    for _ in range(8):
        gate.select(
            candidates=("eat", "rest"),
            base_scores={"eat": 0.5, "rest": 0.2},
            deliberation=deliberation,
            retrieved_boost={},
            rng=rng,
        )
    assert gate.habits.get("eat", 0.0) > 0.0


def test_cerebellum_smooths_repeated_action():
    cb = CerebellarCoordinator(buffer_size=5, min_consensus=3)
    for _ in range(3):
        cb.correct("rest", confidence=0.6)
    action, conf = cb.correct("eat", confidence=0.7)
    assert action == "rest"
    assert conf <= 0.7


def test_goal_stack_multi_step_flee():
    stack = GoalStack()
    assert stack.push_plan("flee")
    assert stack.peek_action() == "explore"
    assert stack.advance_if_matched("explore")
    assert stack.peek_action() == "flee"


def test_integrated_executive_emits_deliberation():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=40,
            perception_mode="predictive",
            memory_mode="integrated",
            executive_mode="integrated",
            profile="test_v5",
        )
    )
    result = rt.run()
    types = {e.event_type for e in rt.state_store.event_log}
    assert "deliberation.completed" in types
    assert result["executive_mode"] == "integrated"
    assert result["deliberation_events"] > 0


def test_executive_integrated_vs_legacy_metrics():
    legacy = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=50,
            perception_mode="predictive",
            memory_mode="integrated",
            executive_mode="legacy",
        )
    ).run()
    integrated = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=50,
            perception_mode="predictive",
            memory_mode="integrated",
            executive_mode="integrated",
        )
    ).run()
    assert legacy["deliberation_events"] == 0
    assert integrated["deliberation_events"] > 0


def test_executive_reproducible():
    cfg = dict(
        seed=88,
        ticks=35,
        perception_mode="predictive",
        memory_mode="integrated",
        executive_mode="integrated",
    )
    r1 = IntegratedRuntime(IntegratedRuntimeConfig(**cfg)).run()
    r2 = IntegratedRuntime(IntegratedRuntimeConfig(**cfg)).run()
    assert r1["trajectory_hash"] == r2["trajectory_hash"]
    assert r1["deliberation_events"] == r2["deliberation_events"]


def test_integrated_v5_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v5.yaml")
    result = rt.run(40)
    assert result["profile"] == "integrated_v5"
    assert result["executive_mode"] == "integrated"
    assert result["memory_mode"] == "integrated"
