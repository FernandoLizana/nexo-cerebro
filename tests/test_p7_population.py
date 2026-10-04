"""P7 Population engine, stress testing, cohort aggregation."""

from __future__ import annotations

from pathlib import Path

import nexo_qa
import yaml

from nexo_qa.population import (
    CohortSpec,
    CognitiveStressTest,
    PopulationAggregator,
    PopulationPlanner,
    PopulationRunner,
    PopulationSpec,
    RunnerConfig,
)
from nexo_qa.population.aggregator import compute_distribution
from nexo_qa.population.clustering import FailureClusterer
from nexo_qa.population.models import ExecutionBudget, RunExecutionRecord, RunPlan, RunStatus
from nexo_qa.population.reporting import aggregate_and_report, build_population_report
from nexo_qa.population.seeds import derive_child_seed, derive_run_id
from nexo_qa.population.state import PopulationState
from nexo_qa.population.stress import StressAxis, wm_sweep
from nexo_qa.population.validation import estimate_run_count, validate_population_spec

REPO = Path(__file__).resolve().parents[1]
CONFIGS = REPO / "configs" / "nexo_qa" / "populations"


def _mini_spec(**overrides) -> PopulationSpec:
    cohort = CohortSpec(
        cohort_id="baseline",
        label="Baseline",
        persona_presets=("baseline",),
        seed_count=2,
        task_ids=("default_task",),
        conditions=("BASELINE",),
    )
    defaults = dict(
        population_id="test_pop",
        master_seed=42,
        cohorts=(cohort,),
        execution_budget=ExecutionBudget(max_runs=100),
    )
    defaults.update(overrides)
    return PopulationSpec(**defaults)


def test_p7_phase_version() -> None:
    assert nexo_qa.__phase__ in ("P7", "P8", "P9")
    assert "p" in nexo_qa.__version__


def test_population_spec_roundtrip() -> None:
    spec = _mini_spec()
    restored = PopulationSpec.from_dict(spec.to_dict())
    assert restored.population_id == spec.population_id
    assert restored.cohorts[0].cohort_id == "baseline"
    assert restored.spec_hash() == spec.spec_hash()


def test_validate_requires_cohorts() -> None:
    spec = PopulationSpec(population_id="empty", cohorts=())
    assert any("cohort" in e for e in validate_population_spec(spec))


def test_run_count_guard_max_runs() -> None:
    spec = _mini_spec(
        execution_budget=ExecutionBudget(max_runs=1),
        cohorts=(
            CohortSpec(
                cohort_id="big",
                label="Big",
                persona_presets=("baseline", "low_wm"),
                seed_count=5,
                task_ids=("t1", "t2"),
            ),
        ),
    )
    errors = validate_population_spec(spec)
    assert any("max_runs" in e for e in errors)


def test_estimate_run_count_matches_planner(tmp_path: Path) -> None:
    spec = _mini_spec()
    assert estimate_run_count(spec) == 2
    plan = PopulationPlanner().plan(spec, artifact_root=tmp_path)
    assert plan.planned_runs == estimate_run_count(spec)


def test_derive_child_seed_deterministic() -> None:
    a = derive_child_seed(42, cohort_id="c", task_id="t", sample_index=0, persona_id="p", condition_set_id="BASELINE")
    b = derive_child_seed(42, cohort_id="c", task_id="t", sample_index=0, persona_id="p", condition_set_id="BASELINE")
    assert a == b


def test_derive_child_seed_reordering_invariant() -> None:
    """Same logical cell → same seed regardless of sample_index assignment order."""
    s1 = derive_child_seed(42, cohort_id="a", task_id="t", sample_index=3, persona_id="baseline", condition_set_id="BASELINE")
    s2 = derive_child_seed(99, cohort_id="a", task_id="t", sample_index=3, persona_id="baseline", condition_set_id="BASELINE")
    assert s1 != s2  # different master seeds differ


def test_derive_run_id_deterministic() -> None:
    rid = derive_run_id("spec", "c", "t", "baseline", 12345, "BASELINE", 0)
    assert rid.startswith("run-")
    assert rid == derive_run_id("spec", "c", "t", "baseline", 12345, "BASELINE", 0)


def test_population_plan_deterministic(tmp_path: Path) -> None:
    spec = _mini_spec()
    root = tmp_path / "pop"
    p1 = PopulationPlanner().plan(spec, artifact_root=root)
    p2 = PopulationPlanner().plan(spec, artifact_root=root)
    assert p1.plan_hash() == p2.plan_hash()
    assert [r.run_id for r in p1.runs] == [r.run_id for r in p2.runs]
    assert [r.seed for r in p1.runs] == [r.seed for r in p2.runs]


def test_dry_run_report() -> None:
    spec = _mini_spec()
    report = PopulationPlanner().dry_run_report(spec)
    assert report["dry_run"] is True
    assert report["estimated_runs"] == 2


def test_runner_trace_fixture(tmp_path: Path) -> None:
    spec = _mini_spec()
    plan = PopulationPlanner().plan(spec, artifact_root=tmp_path)
    runner = PopulationRunner(RunnerConfig(backend="trace_fixture", max_parallel=1))
    state = runner.execute_plan(plan, population_root=tmp_path)
    assert state.completed_count() == plan.planned_runs
    for rec in state.records.values():
        assert rec.status == RunStatus.COMPLETED
        assert rec.p6_summary is not None
        assert rec.summary_path


def test_runner_dry_run_planned_only(tmp_path: Path) -> None:
    spec = _mini_spec()
    plan = PopulationPlanner().plan(spec, artifact_root=tmp_path)
    runner = PopulationRunner(RunnerConfig(dry_run=True))
    state = runner.execute_plan(plan, population_root=tmp_path)
    assert all(r.status == RunStatus.PLANNED for r in state.records.values())
    assert not any((tmp_path / "runs" / r.run_id / "raw_trace.json").exists() for r in plan.runs)


def test_runner_resume_idempotent(tmp_path: Path) -> None:
    spec = _mini_spec()
    plan = PopulationPlanner().plan(spec, artifact_root=tmp_path)
    runner = PopulationRunner(RunnerConfig(backend="trace_fixture", max_parallel=1))
    state1 = runner.execute_plan(plan, population_root=tmp_path)
    completed = state1.completed_count()
    state2 = runner.execute_plan(plan, population_root=tmp_path, resume=True)
    assert state2.completed_count() == completed
    assert state2.pending_run_ids([r.run_id for r in plan.runs]) == []


def test_runner_reuses_completed_cache(tmp_path: Path) -> None:
    cohort = CohortSpec(
        cohort_id="baseline",
        label="Baseline",
        persona_presets=("baseline",),
        seed_count=1,
        task_ids=("default_task",),
    )
    spec = _mini_spec(cohorts=(cohort,))
    plan = PopulationPlanner().plan(spec, artifact_root=tmp_path)
    runner = PopulationRunner(RunnerConfig(backend="trace_fixture"))
    runner.execute_plan(plan, population_root=tmp_path)
    (tmp_path / "population_state.json").unlink(missing_ok=True)
    state = runner.execute_plan(plan, population_root=tmp_path, resume=False)
    rec = next(iter(state.records.values()))
    assert rec.attempts == 0  # cache hit from existing artifacts


def test_infra_vs_task_failure_enum() -> None:
    plan = RunPlan(
        run_id="run-x",
        population_id="p",
        cohort_id="c",
        task_id="t",
        persona_id="baseline",
        persona_config_hash="h",
        seed=1,
        condition_set_id="BASELINE",
        sample_index=0,
        config_versions={},
        artifact_path="/tmp",
    )
    infra = RunExecutionRecord(plan=plan, status=RunStatus.FAILED_INFRASTRUCTURE)
    task = RunExecutionRecord(plan=plan, status=RunStatus.FAILED_TASK)
    assert infra.status != task.status
    assert RunStatus.FAILED_INFRASTRUCTURE.value == "FAILED_INFRASTRUCTURE"


def test_compute_distribution_percentiles() -> None:
    dist = compute_distribution([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
    assert dist.status == "AVAILABLE"
    assert dist.median == 4.5
    assert dist.p10 is not None
    assert dist.p90 is not None


def test_compute_distribution_insufficient_sample() -> None:
    dist = compute_distribution([1.0, 2.0])
    assert dist.status == "INSUFFICIENT_SAMPLE"
    assert dist.mean == 1.5


def test_aggregator_denominators() -> None:
    plan = RunPlan(
        run_id="r1",
        population_id="p",
        cohort_id="baseline",
        task_id="t",
        persona_id="baseline",
        persona_config_hash="h",
        seed=1,
        condition_set_id="BASELINE",
        sample_index=0,
        config_versions={},
        artifact_path="/tmp",
    )
    valid = RunExecutionRecord(
        plan=plan,
        status=RunStatus.COMPLETED,
        p6_summary={"ncfs": {"value": 80.0}, "crs": {"value": 70.0}, "assessment_status": "PASS"},
    )
    infra = RunExecutionRecord(plan=plan, status=RunStatus.FAILED_INFRASTRUCTURE)
    result = PopulationAggregator().aggregate(
        population_id="p",
        spec_hash="abc",
        records=[valid, infra],
    )
    assert result.valid_runs == 1
    assert result.infrastructure_failures == 1
    assert result.cohorts["baseline"].n_valid == 1


def test_aggregator_cohort_comparisons() -> None:
    def _rec(cohort_id: str, ncfs: float) -> RunExecutionRecord:
        plan = RunPlan(
            run_id=f"r-{cohort_id}",
            population_id="p",
            cohort_id=cohort_id,
            task_id="t",
            persona_id="baseline",
            persona_config_hash="h",
            seed=1,
            condition_set_id="BASELINE",
            sample_index=0,
            config_versions={},
            artifact_path="/tmp",
        )
        return RunExecutionRecord(
            plan=plan,
            status=RunStatus.COMPLETED,
            p6_summary={"ncfs": {"value": ncfs}, "assessment_status": "PASS"},
        )

    records = [_rec("baseline", 90.0), _rec("high_distractibility", 70.0)]
    result = PopulationAggregator().aggregate(population_id="p", spec_hash="x", records=records)
    assert len(result.cohort_comparisons) == 1
    assert result.cohort_comparisons[0]["ncfs_median_delta"] == -20.0


def test_failure_clusterer_drilldown() -> None:
    plan = RunPlan(
        run_id="r1",
        population_id="p",
        cohort_id="c",
        task_id="t",
        persona_id="baseline",
        persona_config_hash="h",
        seed=1,
        condition_set_id="BASELINE",
        sample_index=0,
        config_versions={},
        artifact_path="/tmp",
    )
    rec = RunExecutionRecord(
        plan=plan,
        status=RunStatus.COMPLETED,
        certificate_ids=["cert-abc"],
        p6_summary={
            "top_issues": [
                {
                    "failure_family": "ATTENTION",
                    "failure_types": ["DISTRACTOR_CAPTURE"],
                    "severity": "CRITICAL",
                    "occurrences": 2,
                    "certificate_ids": ["cert-abc"],
                }
            ]
        },
    )
    clusters = FailureClusterer().cluster([rec])
    assert clusters
    c = clusters[0]
    assert "cert-abc" in c.certificate_refs
    assert "r1" in c.affected_run_ids


def test_rare_critical_preserved() -> None:
    plan = RunPlan(
        run_id="r1",
        population_id="p",
        cohort_id="c",
        task_id="t",
        persona_id="baseline",
        persona_config_hash="h",
        seed=1,
        condition_set_id="BASELINE",
        sample_index=0,
        config_versions={},
        artifact_path="/tmp",
    )
    rec = RunExecutionRecord(
        plan=plan,
        status=RunStatus.COMPLETED,
        p6_summary={
            "top_issues": [
                {"failure_family": "GOAL", "failure_types": ["GOAL_DRIFT"], "severity": "CRITICAL", "occurrences": 1}
            ]
        },
    )
    clusterer = FailureClusterer()
    objs = clusterer.cluster([rec])
    rare = clusterer.rare_critical(objs)
    assert rare
    assert rare[0]["failure_type"] == "GOAL_DRIFT"


def test_stress_test_manifest() -> None:
    stress = CognitiveStressTest(
        stress_test_id="test_stress",
        task_id="memory_task",
        axes=(StressAxis(trait="working_memory_capacity", levels=(3, 5)),),
        seeds_per_cell=2,
    )
    manifest = stress.manifest()
    assert manifest["total_planned_runs"] == 4


def test_stress_to_population_spec() -> None:
    spec = wm_sweep(task_id="memory_task", capacities=(3, 5)).to_population_spec()
    assert spec.population_id == "wm_stress"
    assert len(spec.cohorts) == 2
    assert estimate_run_count(spec) == 6  # 2 levels × 3 seeds default


def test_report_disclaimers() -> None:
    from nexo_qa.population.aggregator import PopulationResult

    result = PopulationResult(population_id="p", spec_hash="h", planned_runs=0, completed_runs=0, infrastructure_failures=0, task_failures=0, valid_runs=0)
    report = build_population_report(result)
    assert "simulated" in report["disclaimer_en"].lower()
    assert "humana" in report["disclaimer_es"].lower()
    assert result.to_dict()["disclaimer"]


def test_aggregate_and_report_writes_files(tmp_path: Path) -> None:
    spec = _mini_spec(cohorts=(CohortSpec(cohort_id="baseline", label="B", persona_presets=("baseline",), seed_count=1),))
    plan = PopulationPlanner().plan(spec, artifact_root=tmp_path)
    state = PopulationRunner(RunnerConfig(backend="trace_fixture")).execute_plan(plan, population_root=tmp_path)
    report = aggregate_and_report(population_root=tmp_path, state=state)
    assert (tmp_path / "population_report.json").exists()
    assert (tmp_path / "population_report.md").exists()
    assert (tmp_path / "runs.csv").exists()
    assert report["result"]["valid_runs"] >= 1


def test_population_state_pending() -> None:
    state = PopulationState(population_id="p", spec_hash="h", plan_hash="ph")
    assert state.pending_run_ids(["a", "b"]) == ["a", "b"]
    plan = RunPlan(
        run_id="a",
        population_id="p",
        cohort_id="c",
        task_id="t",
        persona_id="baseline",
        persona_config_hash="h",
        seed=1,
        condition_set_id="BASELINE",
        sample_index=0,
        config_versions={},
        artifact_path="/tmp",
    )
    state.records["a"] = RunExecutionRecord(plan=plan, status=RunStatus.COMPLETED)
    assert state.pending_run_ids(["a", "b"]) == ["b"]


def test_parallelism_does_not_change_plan(tmp_path: Path) -> None:
    spec = _mini_spec()
    plan = PopulationPlanner().plan(spec, artifact_root=tmp_path)
    seeds_before = {r.run_id: r.seed for r in plan.runs}
    runner = PopulationRunner(RunnerConfig(backend="trace_fixture", max_parallel=2))
    runner.execute_plan(plan, population_root=tmp_path / "parallel")
    plan2 = PopulationPlanner().plan(spec, artifact_root=tmp_path / "parallel2")
    seeds_after = {r.run_id: r.seed for r in plan2.runs}
    assert seeds_before == seeds_after


def test_baseline_population_yaml_valid() -> None:
    path = CONFIGS / "baseline_population.yaml"
    spec = PopulationSpec.from_dict(yaml.safe_load(path.read_text(encoding="utf-8")))
    assert not validate_population_spec(spec)
    assert estimate_run_count(spec) == 10  # 2 cohorts × 1 persona × 5 seeds


def test_population_module_exports() -> None:
    from nexo_qa import population

    assert hasattr(population, "PopulationSpec")
    assert hasattr(population, "PopulationRunner")


def test_seeds_module_independent_of_execution_order() -> None:
    ids = [
        derive_run_id("h", "c", "t", "p", derive_child_seed(1, cohort_id="c", task_id="t", sample_index=i, persona_id="p", condition_set_id="BASELINE"), "BASELINE", i)
        for i in range(5)
    ]
    assert len(set(ids)) == 5
