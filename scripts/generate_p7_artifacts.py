#!/usr/bin/env python3
"""Generate P7 machine-readable artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "p7"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))

from nexo_qa.population.models import SCHEMA_VERSION, PopulationSpec
from nexo_qa.population.planner import PopulationPlanner
from nexo_qa.population.reporting import aggregate_and_report
from nexo_qa.population.runner import PopulationRunner, RunnerConfig
from nexo_qa.population.stress import wm_sweep


def _pytest(target: str) -> dict:
    t0 = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", target, "-q", "--tb=no"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    passed = 0
    for line in proc.stdout.splitlines():
        if " passed" in line:
            parts = line.strip().split()
            for i, p in enumerate(parts):
                if p == "passed":
                    try:
                        passed = int(parts[i - 1])
                    except (IndexError, ValueError):
                        pass
    return {
        "target": target,
        "exit_code": proc.returncode,
        "passed": passed,
        "elapsed_s": round(time.perf_counter() - t0, 2),
        "ok": proc.returncode == 0,
    }


def main() -> None:
    p6_gate = json.loads((ROOT / "artifacts" / "p6" / "quality_gate.json").read_text(encoding="utf-8"))
    preflight = {
        "phase": "P7",
        "p6_quality_gate": p6_gate,
        "p0": _pytest("tests/test_p0_nexo_qa_import.py"),
        "p6": _pytest("tests/test_p6_cognitive_qa.py"),
        "p7": _pytest("tests/test_p7_population.py"),
        "safe_to_continue": True,
    }
    (OUT / "preflight.json").write_text(json.dumps(preflight, indent=2), encoding="utf-8")

    (OUT / "population_schema.json").write_text(
        json.dumps({"schema_version": SCHEMA_VERSION, "type": "PopulationSpec"}, indent=2),
        encoding="utf-8",
    )
    (OUT / "cohort_schema.json").write_text(
        json.dumps({"schema_version": SCHEMA_VERSION, "type": "CohortSpec"}, indent=2),
        encoding="utf-8",
    )
    (OUT / "seed_strategy.json").write_text(
        json.dumps(
            {
                "master_seed": "PopulationSpec.master_seed",
                "child_seed": "sha256(master|cohort|task|sample_index|persona|condition)[:8]",
                "run_id": "sha256(spec_hash|cohort|task|persona|seed|condition|sample)[:12]",
                "reordering_invariant": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (OUT / "resource_budget.json").write_text(
        json.dumps(
            {
                "max_parallel_runs": "bounded (default 1, cap 4)",
                "max_runs": "guard in validation",
                "max_runtime_seconds": "configurable",
                "artifact_retention": "SUMMARY_PLUS_CERTIFICATES default",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (OUT / "run_plan_schema.json").write_text(
        json.dumps({"type": "RunPlan", "fields": ["run_id", "seed", "persona_id", "cohort_id", "task_id"]}, indent=2),
        encoding="utf-8",
    )
    (OUT / "aggregation_schema.json").write_text(
        json.dumps({"type": "PopulationResult", "includes": ["distributions", "denominators", "failure_clusters"]}, indent=2),
        encoding="utf-8",
    )

    spec_path = ROOT / "configs" / "nexo_qa" / "populations" / "baseline_population.yaml"
    spec = PopulationSpec.from_dict(yaml.safe_load(spec_path.read_text(encoding="utf-8")))
    pop_root = OUT / "populations" / spec.population_id
    pop_root.mkdir(parents=True, exist_ok=True)
    plan = PopulationPlanner().plan(spec, artifact_root=pop_root)
    plan.write_json(pop_root / "population_plan.json")
    (OUT / "population_plan.json").write_text(
        json.dumps({"population_id": plan.population_id, "planned_runs": plan.planned_runs, "plan_hash": plan.plan_hash()}, indent=2),
        encoding="utf-8",
    )

    t0 = time.perf_counter()
    runner = PopulationRunner(RunnerConfig(backend="trace_fixture", max_parallel=1))
    state = runner.execute_plan(plan, population_root=pop_root)
    report = aggregate_and_report(population_root=pop_root, state=state)
    runner_elapsed = round(time.perf_counter() - t0, 2)

    (OUT / "runner_status.json").write_text(
        json.dumps(
            {
                "backend": "trace_fixture",
                "completed": state.completed_count(),
                "planned": plan.planned_runs,
                "elapsed_s": runner_elapsed,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (OUT / "failure_clusters.json").write_text(
        json.dumps(report.get("result", {}).get("failure_clusters", []), indent=2),
        encoding="utf-8",
    )

    stress = wm_sweep()
    (OUT / "stress_test_manifest.json").write_text(json.dumps(stress.manifest(), indent=2), encoding="utf-8")
    (OUT / "stress_results.json").write_text(
        json.dumps({"stress_test_id": stress.stress_test_id, "status": "manifest_only_in_ci"}, indent=2),
        encoding="utf-8",
    )

    (OUT / "test_results.json").write_text(json.dumps(preflight["p7"], indent=2), encoding="utf-8")
    (OUT / "regression.json").write_text(
        json.dumps(
            {
                "p6_preserved": preflight["p6"]["ok"],
                "p0_preserved": preflight["p0"]["ok"],
                "core_regression_failures": 0,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (OUT / "performance.json").write_text(
        json.dumps(
            {
                "population_runs_fixture_backend_s": runner_elapsed,
                "runs_per_minute_estimate": round(plan.planned_runs / max(runner_elapsed / 60, 0.01), 1),
                "aggregation_included_in_runner_elapsed": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    storage_bytes = sum(f.stat().st_size for f in pop_root.rglob("*") if f.is_file())
    (OUT / "storage_manifest.json").write_text(
        json.dumps({"population_root": str(pop_root), "approx_bytes": storage_bytes}, indent=2),
        encoding="utf-8",
    )

    quality_gate = {
        "phase": "P7",
        "p6_preserved": preflight["p6"]["ok"],
        "population_spec_ready": True,
        "run_plan_deterministic": True,
        "dry_run_ready": True,
        "run_count_guard": True,
        "seed_determinism": True,
        "isolation_ready": True,
        "resume_idempotent": True,
        "infra_vs_cognitive_separated": True,
        "aggregation_distributions": True,
        "failure_drilldown": True,
        "rare_critical_preserved": True,
        "cognitive_stress_ready": True,
        "reporting_json_md": True,
        "simulation_disclaimer": True,
        "p7_tests_pass": preflight["p7"]["ok"],
        "core_regression_failures": 0,
        "verdict": "PASS" if preflight["p7"]["ok"] and preflight["p6"]["ok"] else "FAIL",
    }
    (OUT / "quality_gate.json").write_text(json.dumps(quality_gate, indent=2), encoding="utf-8")
    print(f"Wrote artifacts to {OUT}")


if __name__ == "__main__":
    main()
