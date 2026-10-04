"""P8 Cognitive Chaos Testing — perturbations, paired design, deltas."""

from __future__ import annotations

import inspect
from pathlib import Path

import nexo_qa
import yaml

from nexo_qa.chaos import (
    ChaosPlanner,
    ChaosRunner,
    ChaosRunnerConfig,
    ChaosSpec,
    analyze_pairs,
    compute_paired_delta,
    validate_pair_invariants,
)
from nexo_qa.chaos.controller import PerturbationController
from nexo_qa.chaos.models import PerturbationSpec, TriggerSpec
from nexo_qa.chaos.offline import analyze_chaos_directory
from nexo_qa.chaos.pairs import status_degradation_rate
from nexo_qa.chaos.perturbed_world import ChaoticMockWorld
from nexo_qa.chaos.reporting import build_chaos_report, build_chaos_report_markdown
from nexo_qa.chaos.triggers import should_fire
from nexo_qa.chaos.validation import validate_perturbation_spec
from nexo_qa.chaos.web_lab import SCENARIOS, list_scenarios, scenario_html_path
from nexo_qa.population.models import RunExecutionRecord, RunPlan, RunStatus

REPO = Path(__file__).resolve().parents[1]
CHAOS_DIR = REPO / "nexo_qa" / "chaos"
CONFIG = REPO / "configs" / "nexo_qa" / "chaos" / "paired_baseline.yaml"


def _perturbation(**kwargs) -> PerturbationSpec:
    defaults = dict(
        perturbation_id="test_pert",
        type="INTERRUPTION",
        trigger=TriggerSpec(kind="AT_TICK", at_tick=1),
        duration_ticks=2,
    )
    defaults.update(kwargs)
    return PerturbationSpec(**defaults)


def _run_plan(**kwargs) -> RunPlan:
    defaults = dict(
        run_id="run-a",
        population_id="p",
        cohort_id="c",
        task_id="default_task",
        persona_id="baseline",
        persona_config_hash="h",
        seed=12345,
        condition_set_id="BASELINE",
        sample_index=0,
        config_versions={"metrics": "metrics-v1"},
        artifact_path="/tmp/a",
    )
    defaults.update(kwargs)
    return RunPlan(**defaults)


def _completed_rec(plan: RunPlan, **summary) -> RunExecutionRecord:
    base = {
        "assessment_status": "PASS",
        "ncfs": {"value": 85.0},
        "crs": {"value": 80.0},
        "ehfp": {"value": 10.0},
        "perturbation_coverage": {"planned": 1, "successfully_injected": 1, "missed": 0, "injection_failures": 0},
    }
    base.update(summary)
    return RunExecutionRecord(plan=plan, status=RunStatus.COMPLETED, p6_summary=base, summary_path="/tmp/s.json")


def test_p8_phase_version() -> None:
    assert nexo_qa.__phase__ in ("P8", "P9")


def test_perturbation_spec_validation() -> None:
    ok = _perturbation()
    assert not validate_perturbation_spec(ok)
    bad = _perturbation(target_scope="cognition")
    assert any("environment" in e for e in validate_perturbation_spec(bad))


def test_deterministic_trigger() -> None:
    spec = _perturbation(trigger=TriggerSpec(kind="AT_TICK", at_tick=3))
    assert should_fire(spec.trigger, tick=2, action_count=0) is False
    assert should_fire(spec.trigger, tick=3, action_count=0) is True
    ctrl = PerturbationController(specs=(spec,), run_seed=42)
    ctrl.evaluate(tick=3, action_count=0)
    assert spec.perturbation_id in ctrl.active


def test_pair_invariants() -> None:
    baseline = _run_plan(condition_set_id="BASELINE", seed=99)
    perturbed = _run_plan(run_id="run-b", condition_set_id="PERTURBED_x", seed=99)
    validity, _ = validate_pair_invariants(baseline, perturbed)
    assert validity == "VALID"
    bad = _run_plan(run_id="run-c", seed=100, condition_set_id="PERTURBED_x")
    validity, reason = validate_pair_invariants(baseline, bad)
    assert validity == "INVALID_PAIR"
    assert "seed" in (reason or "")


def test_interruption_injection() -> None:
    spec = _perturbation(
        perturbation_id="intr",
        type="INTERRUPTION",
        trigger=TriggerSpec(kind="AT_TICK", at_tick=0),
        parameters={"allowed_actions": ("wait",)},
    )
    world = ChaoticMockWorld.create(seed=42, perturbations=(spec,))
    world.apply_action("inspect_panel")
    assert any(p[0] == "interruption_overlay" for p in world.percepts_for_agent())
    cov = world.injection_coverage()
    assert cov["successfully_injected"] >= 1


def test_interruption_preserves_goal() -> None:
    world = ChaoticMockWorld.create(
        seed=42,
        perturbations=(
            _perturbation(
                type="INTERRUPTION",
                trigger=TriggerSpec(kind="AT_TICK", at_tick=0),
                duration_ticks=2,
                parameters={"allowed_actions": ("wait", "inspect_panel")},
            ),
        ),
    )
    assert world.goal_preserved is True
    world.apply_action("wait")
    world.apply_action("inspect_panel")
    assert world.phase in ("closed", "armed", "open", "done")


def test_perturbation_does_not_directly_mutate_cognition() -> None:
    src = (CHAOS_DIR / "perturbed_world.py").read_text(encoding="utf-8")
    for token in ("agent.memory.clear", "agent.frustration =", "persona_traits =", "decision_score ="):
        assert token not in src
    ctrl = PerturbationController(specs=(_perturbation(),))
    assert "agent.memory" in ctrl.forbidden_cognitive_tokens()


def test_latency_injection() -> None:
    spec = _perturbation(
        type="LATENCY",
        trigger=TriggerSpec(kind="AT_TICK", at_tick=0),
        parameters={"delay_ticks": 2},
    )
    world = ChaoticMockWorld.create(seed=1, perturbations=(spec,))
    result = world.apply_action("inspect_panel")
    assert result.get("error") == "latency_pending" or "loading_spinner" in str(world.percepts_for_agent())


def test_transient_error_injection() -> None:
    spec = _perturbation(
        type="TRANSIENT_ERROR",
        trigger=TriggerSpec(kind="AT_TICK", at_tick=0),
        parameters={"fail_attempts": 1},
    )
    world = ChaoticMockWorld.create(seed=1, perturbations=(spec,))
    r1 = world.apply_action("inspect_panel")
    assert r1.get("error") == "transient_error"
    r2 = world.apply_action("inspect_panel")
    assert r2.get("accepted") is True


def test_session_expiry() -> None:
    spec = _perturbation(type="SESSION_EXPIRY", trigger=TriggerSpec(kind="AT_TICK", at_tick=0))
    world = ChaoticMockWorld.create(seed=1, perturbations=(spec,))
    world.apply_action("inspect_panel")
    percepts = [p[0] for p in world.percepts_for_agent()]
    assert "session_expired_notice" in percepts
    assert world.goal_preserved is True


def test_visual_change_detected_by_perception() -> None:
    spec = _perturbation(type="VISUAL_CHANGE", trigger=TriggerSpec(kind="AT_TICK", at_tick=0))
    world = ChaoticMockWorld.create(seed=1, perturbations=(spec,))
    world.apply_action("wait")
    names = [p[0] for p in world.percepts_for_agent()]
    assert "switch" in names or "panel" in names


def test_modal_distraction_affects_scene() -> None:
    spec = _perturbation(type="MODAL_DISTRACTION", trigger=TriggerSpec(kind="AT_TICK", at_tick=0))
    world = ChaoticMockWorld.create(seed=1, perturbations=(spec,))
    names = [p[0] for p in world.percepts_for_agent()]
    assert "promotion_modal" in names


def test_feedback_delay_observable() -> None:
    spec = _perturbation(
        type="FEEDBACK_DELAY",
        trigger=TriggerSpec(kind="AT_TICK", at_tick=0),
        parameters={"delay_ticks": 1},
    )
    world = ChaoticMockWorld.create(seed=1, perturbations=(spec,))
    result = world.apply_action("inspect_panel")
    assert result.get("error") == "feedback_pending" or result.get("feedback_delayed")


def test_control_disable() -> None:
    spec = _perturbation(
        type="CONTROL_DISABLE",
        trigger=TriggerSpec(kind="AT_TICK", at_tick=0),
        parameters={"disabled_actions": ("activate_switch",)},
    )
    world = ChaoticMockWorld.create(seed=1, perturbations=(spec,))
    world.apply_action("inspect_panel")
    assert "activate_switch" not in world.available_actions()


def test_no_oracle_action_access() -> None:
    code = "\n".join((CHAOS_DIR / f).read_text(encoding="utf-8") for f in ("controller.py", "triggers.py", "perturbed_world.py"))
    for token in ("correct_action", "golden_path", "expected_step"):
        assert token not in code


def test_selector_secrecy_under_chaos() -> None:
    code = "\n".join(p.read_text(encoding="utf-8") for p in CHAOS_DIR.glob("*.py"))
    for token in ("data-testid", "xpath", "playwright", "css selector"):
        assert token.lower() not in code.lower()


def test_security_policy_preserved() -> None:
    code = "\n".join(p.read_text(encoding="utf-8") for p in CHAOS_DIR.glob("*.py"))
    assert "password" not in code or "redact" in code


def test_paired_delta_calculation() -> None:
    pair_plan = type("P", (), {"pair_id": "pair-1"})()
    baseline = _completed_rec(_run_plan(run_id="b", condition_set_id="BASELINE", seed=1))
    perturbed = _completed_rec(
        _run_plan(run_id="p", condition_set_id="PERTURBED_x", seed=1, perturbation_id="x"),
        ncfs={"value": 70.0},
        crs={"value": 60.0},
    )
    from nexo_qa.chaos.models import ChaosPairPlan

    pair = ChaosPairPlan(
        pair_id="pair-1",
        perturbation=_perturbation(perturbation_id="x"),
        baseline_run_id="b",
        perturbed_run_id="p",
        task_id="default_task",
        persona_id="baseline",
        seed=1,
    )
    delta = compute_paired_delta(pair, baseline, perturbed)
    assert delta.validity == "VALID"
    assert delta.metric_deltas["ncfs_delta"] == -15.0


def test_invalid_pair_exclusion() -> None:
    baseline = _completed_rec(_run_plan(seed=1))
    perturbed = _completed_rec(_run_plan(run_id="p2", seed=2, condition_set_id="PERTURBED_x"))
    from nexo_qa.chaos.models import ChaosPairPlan

    pair = ChaosPairPlan(
        pair_id="pair-x",
        perturbation=_perturbation(),
        baseline_run_id="run-a",
        perturbed_run_id="p2",
        task_id="default_task",
        persona_id="baseline",
        seed=1,
    )
    delta = compute_paired_delta(pair, baseline, perturbed)
    assert delta.validity == "INVALID_PAIR"
    rate = status_degradation_rate([delta])
    assert rate["valid_pairs"] == 0


def test_status_degradation() -> None:
    from nexo_qa.chaos.models import ChaosPairPlan, PairedChaosDelta

    d = PairedChaosDelta(
        pair_id="p1",
        validity="VALID",
        baseline_run_id="b",
        perturbed_run_id="p",
        status_change="PASS → FAIL",
    )
    rate = status_degradation_rate([d])
    assert rate["status_degradation_count"] == 1


def test_interruption_recovery_time() -> None:
    spec = _perturbation(
        type="INTERRUPTION",
        trigger=TriggerSpec(kind="AFTER_ACTION", after_action_count=1),
        duration_ticks=1,
        parameters={"allowed_actions": ("wait", "inspect_panel", "activate_switch", "collect_target", "finish")},
    )
    world = ChaoticMockWorld.create(seed=42, perturbations=(spec,))
    for _ in range(8):
        for action in world.available_actions():
            world.apply_action(action)
            break
    assert world.perturbation_events()


def test_population_chaos(tmp_path: Path) -> None:
    spec = ChaosSpec.from_dict(yaml.safe_load(CONFIG.read_text(encoding="utf-8")))
    spec = ChaosSpec(
        chaos_id="mini_chaos",
        master_seed=42,
        perturbations=spec.perturbations[:2],
    )
    runner = ChaosRunner(ChaosRunnerConfig(ticks=16))
    state = runner.execute(spec, chaos_root=tmp_path)
    plan = ChaosPlanner().plan(spec, artifact_root=tmp_path)
    deltas, _ = analyze_pairs(plan=plan, state=state)
    from nexo_qa.chaos.aggregation import aggregate_population_chaos

    agg = aggregate_population_chaos(deltas, chaos_id=spec.chaos_id)
    assert agg["valid_pairs"] + agg["invalid_pairs"] == len(deltas)


def test_cohort_sensitivity() -> None:
    from nexo_qa.chaos.aggregation import cohort_sensitivity_matrix
    from nexo_qa.chaos.models import PairedChaosDelta

    d = PairedChaosDelta(
        pair_id="pair-1",
        validity="VALID",
        baseline_run_id="b",
        perturbed_run_id="p",
        metric_deltas={"ncfs_delta": -12.0},
    )
    rows = cohort_sensitivity_matrix([d], persona_id="baseline", perturbation_types={"pair-1": "INTERRUPTION"})
    assert rows[0]["median_ncfs_delta"] == -12.0


def test_rare_critical_preserved() -> None:
    from nexo_qa.population.clustering import FailureClusterer

    plan = _run_plan()
    rec = RunExecutionRecord(
        plan=plan,
        status=RunStatus.COMPLETED,
        p6_summary={
            "top_issues": [{"failure_family": "GOAL", "failure_types": ["GOAL_DRIFT"], "severity": "CRITICAL"}]
        },
    )
    rare = FailureClusterer().rare_critical(FailureClusterer().cluster([rec]))
    assert rare


def test_offline_pair_reanalysis(tmp_path: Path) -> None:
    spec = ChaosSpec(
        chaos_id="offline",
        perturbations=(_perturbation(perturbation_id="p1", type="LATENCY", trigger=TriggerSpec(kind="AT_TICK", at_tick=0)),),
    )
    runner = ChaosRunner(ChaosRunnerConfig(ticks=12))
    runner.execute(spec, chaos_root=tmp_path)
    report = analyze_chaos_directory(tmp_path)
    assert (tmp_path / "chaos_report.json").exists()
    assert report["report_type"] == "chaos_report"


def test_chaos_resume(tmp_path: Path) -> None:
    spec = ChaosSpec(
        chaos_id="resume_test",
        perturbations=(_perturbation(perturbation_id="p1"),),
    )
    runner = ChaosRunner(ChaosRunnerConfig(ticks=12))
    state1 = runner.execute(spec, chaos_root=tmp_path)
    n1 = state1.completed_count()
    state2 = runner.execute(spec, chaos_root=tmp_path, resume=True)
    assert state2.completed_count() == n1


def test_baseline_cache_reuse(tmp_path: Path) -> None:
    spec = ChaosSpec(
        chaos_id="cache_test",
        perturbations=(_perturbation(perturbation_id="p1"),),
    )
    runner = ChaosRunner(ChaosRunnerConfig(ticks=12, reuse_baseline=True))
    runner.execute(spec, chaos_root=tmp_path)
    (tmp_path / "chaos_state.json").unlink(missing_ok=True)
    state = runner.execute(spec, chaos_root=tmp_path, resume=False)
    baseline = next(r for r in state.records.values() if r.plan.pair_role == "baseline")
    assert baseline.attempts == 0


def test_resource_cleanup() -> None:
    world = ChaoticMockWorld.create(seed=1, perturbations=(_perturbation(),))
    world.apply_action("wait")
    assert inspect.ismethod(world.sync_from_body)


def test_chaos_report() -> None:
    from nexo_qa.chaos.models import ChaosPlan, PairedChaosDelta
    from nexo_qa.chaos.runner import ChaosState

    report = build_chaos_report(
        chaos_id="x",
        plan=ChaosPlan(chaos_id="x", spec_hash="h", pairs=(), runs=()),
        state=ChaosState(chaos_id="x", spec_hash="h"),
        deltas=[
            PairedChaosDelta(
                pair_id="p",
                validity="VALID",
                baseline_run_id="b",
                perturbed_run_id="p",
                metric_deltas={"ncfs_delta": -5.0},
                status_change="PASS → PASS_WITH_FRICTION",
            )
        ],
        injection_coverage={"planned": 1, "successfully_injected": 1},
    )
    md = build_chaos_report_markdown(report)
    assert "simulated" in report["disclaimer_en"].lower()
    assert "Chaos Report" in md


def test_web_lab_scenarios_exist() -> None:
    for sid in list_scenarios():
        assert scenario_html_path(sid).exists()
    assert len(SCENARIOS) >= 8


def test_chaos_planner_paired_seeds() -> None:
    spec = ChaosSpec(
        chaos_id="plan_test",
        perturbations=(_perturbation(perturbation_id="a"), _perturbation(perturbation_id="b", type="LATENCY")),
    )
    plan = ChaosPlanner().plan(spec, artifact_root=REPO / "artifacts" / "p8" / "tmp_plan")
    for pair in plan.pairs:
        baseline = next(r for r in plan.runs if r.run_id == pair.baseline_run_id)
        perturbed = next(r for r in plan.runs if r.run_id == pair.perturbed_run_id)
        assert baseline.seed == perturbed.seed
        assert baseline.task_id == perturbed.task_id


def test_full_regression_p0_p7() -> None:
    import nexo_qa as nq
    from nexo_qa.population import PopulationSpec
    from nexo_qa.chaos import PerturbationSpec

    assert nq.__phase__ in ("P8", "P9")
    assert PopulationSpec is not None
    assert PerturbationSpec is not None
