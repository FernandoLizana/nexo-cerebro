"""Chaos runner — paired execution with baseline cache reuse."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig
from nexo_qa.analysis import analyze_raw_trace, capture_run_trace
from nexo_qa.chaos.models import ChaosPlan, ChaosSpec, PerturbationSpec
from nexo_qa.chaos.perturbed_world import ChaoticMockWorld
from nexo_qa.chaos.planner import ChaosPlanner
from nexo_qa.goals import parse_goal
from nexo_qa.personas.loader import load_preset
from nexo_qa.personas.runtime import bind_persona
from nexo_qa.population.models import RunExecutionRecord, RunPlan, RunStatus
from nexo_qa.population.runner import PopulationRunner, RunnerConfig
from nexo_qa.testing import bind_task

CONFIGS = Path(__file__).resolve().parents[2] / "configs" / "nexo_qa" / "chaos"


@dataclass
class ChaosState:
    chaos_id: str
    spec_hash: str
    records: dict[str, RunExecutionRecord] = field(default_factory=dict)
    pair_map: dict[str, tuple[str, str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chaos_id": self.chaos_id,
            "spec_hash": self.spec_hash,
            "records": {k: v.to_dict() for k, v in self.records.items()},
            "pair_map": self.pair_map,
        }

    def write_json(self, path: Path | str) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load_json(cls, path: Path | str) -> ChaosState:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        records = {k: RunExecutionRecord.from_dict(v) for k, v in (data.get("records") or {}).items()}
        return cls(
            chaos_id=str(data["chaos_id"]),
            spec_hash=str(data.get("spec_hash", "")),
            records=records,
            pair_map={k: tuple(v) for k, v in (data.get("pair_map") or {}).items()},
        )

    def completed_count(self) -> int:
        return sum(1 for r in self.records.values() if r.status == RunStatus.COMPLETED)


@dataclass
class ChaosRunnerConfig:
    dry_run: bool = False
    reuse_baseline: bool = True
    ticks: int = 24
    backend: str = "chaos_mock_world"


class ChaosRunner:
    def __init__(self, config: ChaosRunnerConfig | None = None) -> None:
        self.config = config or ChaosRunnerConfig()
        self._perturbation_catalog: dict[str, PerturbationSpec] = {}

    def load_spec(self, path: Path | str) -> ChaosSpec:
        import yaml

        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        spec = ChaosSpec.from_dict(data)
        for p in spec.perturbations:
            self._perturbation_catalog[p.perturbation_id] = p
        return spec

    def execute(
        self,
        spec: ChaosSpec,
        *,
        chaos_root: Path | str,
        resume: bool = False,
    ) -> ChaosState:
        root = Path(chaos_root)
        root.mkdir(parents=True, exist_ok=True)
        planner = ChaosPlanner()
        plan = planner.plan(spec, artifact_root=root)
        plan.write_json(root / "chaos_plan.json")

        state_path = root / "chaos_state.json"
        state = ChaosState(chaos_id=spec.chaos_id, spec_hash=plan.spec_hash)
        state.pair_map = {p.pair_id: (p.baseline_run_id, p.perturbed_run_id) for p in plan.pairs}
        if resume and state_path.exists():
            state = ChaosState.load_json(state_path)

        if self.config.dry_run:
            for run in plan.runs:
                if run.run_id not in state.records:
                    state.records[run.run_id] = RunExecutionRecord(plan=run, status=RunStatus.PLANNED)
            state.write_json(state_path)
            return state

        for pair in plan.pairs:
            baseline_run = next(r for r in plan.runs if r.run_id == pair.baseline_run_id)
            perturbed_run = next(r for r in plan.runs if r.run_id == pair.perturbed_run_id)

            if baseline_run.run_id not in state.records or state.records[baseline_run.run_id].status != RunStatus.COMPLETED:
                cached = self._try_cache(baseline_run) if self.config.reuse_baseline else None
                state.records[baseline_run.run_id] = cached or self._execute_run(
                    baseline_run, perturbations=(), root=root
                )
                state.write_json(state_path)

            if perturbed_run.run_id not in state.records or state.records[perturbed_run.run_id].status != RunStatus.COMPLETED:
                if resume and perturbed_run.run_id in state.records and state.records[perturbed_run.run_id].status == RunStatus.COMPLETED:
                    continue
                state.records[perturbed_run.run_id] = self._execute_run(
                    perturbed_run,
                    perturbations=(pair.perturbation,),
                    root=root,
                )
                state.write_json(state_path)
        return state

    def _execute_run(
        self,
        run_plan: RunPlan,
        *,
        perturbations: tuple[PerturbationSpec, ...],
        root: Path,
    ) -> RunExecutionRecord:
        run_dir = root / "runs" / run_plan.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        rt = IntegratedRuntime(
            IntegratedRuntimeConfig(
                seed=run_plan.seed,
                ticks=self.config.ticks,
                executive_mode="integrated",
                perception_mode="predictive",
            )
        )
        world = ChaoticMockWorld.create(seed=run_plan.seed, perturbations=perturbations, trace_id=run_plan.run_id)
        goal = parse_goal(f"Complete task {run_plan.task_id}")
        bind_task(rt, goal=goal, world=world)
        persona = load_preset(run_plan.persona_id)
        bind_persona(rt, persona, world=world)
        rt.run()
        raw = capture_run_trace(rt, world=world, run_id=run_plan.run_id)
        raw.metadata["persona_id"] = run_plan.persona_id
        raw.metadata["task_id"] = run_plan.task_id
        raw.metadata["condition_set_id"] = run_plan.condition_set_id
        raw.metadata["pair_id"] = run_plan.pair_id
        raw.metadata["pair_role"] = run_plan.pair_role
        raw.metadata["perturbation_events"] = world.perturbation_events()
        trace_path = run_dir / "raw_trace.json"
        trace_path.write_text(json.dumps(raw.to_dict(), indent=2), encoding="utf-8")
        analysis = analyze_raw_trace(raw, output_dir=run_dir)
        summary = analysis.summary.to_dict() if analysis.summary else {}
        summary["perturbation_coverage"] = world.injection_coverage()
        if world.interruption_recovery_ticks() is not None:
            summary["interruption_recovery"] = {"ticks_to_progress": world.interruption_recovery_ticks()}
        summary_path = str(run_dir / "cognitive_qa_report.json")
        if Path(summary_path).exists():
            report = json.loads(Path(summary_path).read_text(encoding="utf-8"))
            report["summary"] = summary
            Path(summary_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
        return RunExecutionRecord(
            plan=run_plan,
            status=RunStatus.COMPLETED,
            attempts=1,
            summary_path=summary_path,
            trace_path=str(trace_path),
            certificate_ids=[c.certificate_id for c in analysis.certificates],
            p6_summary=summary,
        )

    def _try_cache(self, run_plan: RunPlan) -> RunExecutionRecord | None:
        summary_path = Path(run_plan.artifact_path) / "cognitive_qa_report.json"
        if not summary_path.exists():
            return None
        report = json.loads(summary_path.read_text(encoding="utf-8"))
        summary = report.get("summary") or {}
        return RunExecutionRecord(
            plan=run_plan,
            status=RunStatus.COMPLETED,
            attempts=0,
            summary_path=str(summary_path),
            trace_path=str(Path(run_plan.artifact_path) / "raw_trace.json"),
            certificate_ids=list(summary.get("certificate_ids") or []),
            p6_summary=summary,
        )
