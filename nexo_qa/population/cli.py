"""Population engine CLI — plan, run, resume, aggregate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from nexo_qa.population.models import PopulationSpec
from nexo_qa.population.planner import PopulationPlan, PopulationPlanner
from nexo_qa.population.reporting import aggregate_and_report
from nexo_qa.population.runner import PopulationRunner, RunnerConfig
from nexo_qa.population.state import PopulationState


def _load_spec(path: Path) -> PopulationSpec:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return PopulationSpec.from_dict(data)


def cmd_plan(args: argparse.Namespace) -> int:
    spec = _load_spec(Path(args.config))
    planner = PopulationPlanner()
    if args.dry_run:
        print(json.dumps(planner.dry_run_report(spec), indent=2))
        return 0
    root = Path(args.output or f"artifacts/p7/populations/{spec.population_id}")
    plan = planner.plan(spec, artifact_root=root)
    plan.write_json(root / "population_plan.json")
    print(json.dumps({"planned_runs": plan.planned_runs, "plan_hash": plan.plan_hash()}, indent=2))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    spec = _load_spec(Path(args.config))
    root = Path(args.output or f"artifacts/p7/populations/{spec.population_id}")
    planner = PopulationPlanner()
    plan = (
        PopulationPlan.load_json(root / "population_plan.json")
        if (root / "population_plan.json").exists()
        else planner.plan(spec, artifact_root=root)
    )
    runner = PopulationRunner(
        RunnerConfig(
            dry_run=args.dry_run,
            max_parallel=spec.execution_budget.max_parallel_runs,
            backend=args.backend or "trace_fixture",
        )
    )
    state = runner.execute_plan(plan, population_root=root, resume=args.resume)
    aggregate_and_report(population_root=root, state=state, versions=plan.runs[0].config_versions if plan.runs else {})
    print(json.dumps({"completed": state.completed_count(), "planned": plan.planned_runs}, indent=2))
    return 0


def cmd_aggregate(args: argparse.Namespace) -> int:
    root = Path(args.population_root)
    state = PopulationState.load_json(root / "population_state.json")
    aggregate_and_report(population_root=root, state=state)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nexo-qa-population")
    sub = parser.add_subparsers(dest="command", required=True)

    p_plan = sub.add_parser("plan")
    p_plan.add_argument("config")
    p_plan.add_argument("--output")
    p_plan.add_argument("--dry-run", action="store_true")
    p_plan.set_defaults(func=cmd_plan)

    p_run = sub.add_parser("run")
    p_run.add_argument("config")
    p_run.add_argument("--output")
    p_run.add_argument("--dry-run", action="store_true")
    p_run.add_argument("--resume", action="store_true")
    p_run.add_argument("--backend", choices=["trace_fixture", "mock_world"], default="trace_fixture")
    p_run.set_defaults(func=cmd_run)

    p_agg = sub.add_parser("aggregate")
    p_agg.add_argument("population_root")
    p_agg.set_defaults(func=cmd_aggregate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
