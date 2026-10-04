"""Population runner — resource-aware execution with isolation."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig
from nexo_qa.analysis import analyze_raw_trace, capture_run_trace
from nexo_qa.analysis.models import RawRunTrace
from nexo_qa.goals import parse_goal
from nexo_qa.personas.loader import load_preset
from nexo_qa.personas.runtime import bind_persona
from nexo_qa.population.models import RunExecutionRecord, RunPlan, RunStatus
from nexo_qa.population.planner import PopulationPlan
from nexo_qa.population.state import PopulationState
from nexo_qa.testing import bind_task
from nexo_qa.testing.mock_world import MockWorld

ExecutionBackend = Callable[[RunPlan, Path], RunExecutionRecord]


@dataclass
class RunnerConfig:
    dry_run: bool = False
    max_parallel: int = 1
    max_retries_infra: int = 1
    reuse_completed: bool = True
    backend: str = "mock_world"  # mock_world | trace_fixture


class PopulationRunner:
    def __init__(self, config: RunnerConfig | None = None) -> None:
        self.config = config or RunnerConfig()

    def execute_plan(
        self,
        plan: PopulationPlan,
        *,
        population_root: Path | str,
        state: PopulationState | None = None,
        resume: bool = False,
    ) -> PopulationState:
        root = Path(population_root)
        root.mkdir(parents=True, exist_ok=True)
        plan_path = root / "population_plan.json"
        if not plan_path.exists():
            plan.write_json(plan_path)
        state = state or PopulationState(
            population_id=plan.population_id,
            spec_hash=plan.spec_hash,
            plan_hash=plan.plan_hash(),
        )
        if resume:
            state_path = root / "population_state.json"
            if state_path.exists():
                state = PopulationState.load_json(state_path)

        run_ids = [r.run_id for r in plan.runs]
        pending = state.pending_run_ids(run_ids) if resume else run_ids
        if self.config.dry_run:
            for rp in plan.runs:
                if rp.run_id not in state.records:
                    state.records[rp.run_id] = RunExecutionRecord(plan=rp, status=RunStatus.PLANNED)
            state.write_json(root / "population_state.json")
            return state

        to_run = [r for r in plan.runs if r.run_id in pending]
        parallel = max(1, min(self.config.max_parallel, 4))

        def _execute_one(run_plan: RunPlan) -> RunExecutionRecord:
            if self.config.reuse_completed:
                cached = self._try_cache(run_plan)
                if cached is not None:
                    return cached
            return self._run_with_retry(run_plan, root)

        if parallel == 1:
            for rp in to_run:
                rec = _execute_one(rp)
                state.records[rp.run_id] = rec
                state.write_json(root / "population_state.json")
        else:
            with ThreadPoolExecutor(max_workers=parallel) as pool:
                futures = {pool.submit(_execute_one, rp): rp for rp in to_run}
                for fut in as_completed(futures):
                    rp = futures[fut]
                    state.records[rp.run_id] = fut.result()
                    state.write_json(root / "population_state.json")
        return state

    def _run_with_retry(self, run_plan: RunPlan, root: Path) -> RunExecutionRecord:
        attempts = 0
        last_error = ""
        while attempts <= self.config.max_retries_infra:
            attempts += 1
            try:
                if self.config.backend == "trace_fixture":
                    return self._execute_trace_fixture(run_plan, root)
                return self._execute_mock_world(run_plan, root)
            except OSError as exc:
                last_error = str(exc)
                if attempts > self.config.max_retries_infra:
                    return RunExecutionRecord(
                        plan=run_plan,
                        status=RunStatus.FAILED_INFRASTRUCTURE,
                        attempts=attempts,
                        error=last_error,
                    )
            except Exception as exc:
                return RunExecutionRecord(
                    plan=run_plan,
                    status=RunStatus.FAILED_TASK,
                    attempts=attempts,
                    error=str(exc),
                )
        return RunExecutionRecord(
            plan=run_plan,
            status=RunStatus.FAILED_INFRASTRUCTURE,
            attempts=attempts,
            error=last_error,
        )

    def _execute_mock_world(self, run_plan: RunPlan, root: Path) -> RunExecutionRecord:
        run_dir = root / "runs" / run_plan.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        rt = IntegratedRuntime(
            IntegratedRuntimeConfig(
                seed=run_plan.seed,
                ticks=24,
                executive_mode="integrated",
                perception_mode="predictive",
            )
        )
        world = MockWorld(seed=run_plan.seed)
        goal = parse_goal(f"Complete task {run_plan.task_id}")
        bind_task(rt, goal=goal, world=world)
        persona = load_preset(run_plan.persona_id)
        bind_persona(rt, persona, world=world)
        rt.run()
        raw = capture_run_trace(rt, world=world, run_id=run_plan.run_id)
        raw.metadata["persona_id"] = run_plan.persona_id
        raw.metadata["task_id"] = run_plan.task_id
        trace_path = run_dir / "raw_trace.json"
        trace_path.write_text(json.dumps(raw.to_dict(), indent=2), encoding="utf-8")
        analysis = analyze_raw_trace(raw, output_dir=run_dir)
        summary = analysis.summary.to_dict() if analysis.summary else {}
        cert_ids = [c.certificate_id for c in analysis.certificates]
        summary_path = str(run_dir / "cognitive_qa_report.json")
        return RunExecutionRecord(
            plan=run_plan,
            status=RunStatus.COMPLETED,
            attempts=1,
            summary_path=summary_path,
            trace_path=str(trace_path),
            certificate_ids=cert_ids,
            p6_summary=summary,
        )

    def _execute_trace_fixture(self, run_plan: RunPlan, root: Path) -> RunExecutionRecord:
        fixtures_dir = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "cognitive_qa"
        names = sorted(fixtures_dir.glob("*.json"))
        if not names:
            raise OSError("no trace fixtures")
        pick = names[hash(run_plan.run_id) % len(names)]
        raw = RawRunTrace.from_dict(json.loads(pick.read_text(encoding="utf-8")))
        raw = RawRunTrace(
            run_id=run_plan.run_id,
            seed=run_plan.seed,
            ticks=raw.ticks,
            events=raw.events,
            world_trace=raw.world_trace,
            metadata={**raw.metadata, "persona_id": run_plan.persona_id, "task_id": run_plan.task_id},
        )
        run_dir = root / "runs" / run_plan.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        trace_path = run_dir / "raw_trace.json"
        trace_path.write_text(json.dumps(raw.to_dict(), indent=2), encoding="utf-8")
        analysis = analyze_raw_trace(raw, output_dir=run_dir)
        summary = analysis.summary.to_dict() if analysis.summary else {}
        return RunExecutionRecord(
            plan=run_plan,
            status=RunStatus.COMPLETED,
            attempts=1,
            summary_path=str(run_dir / "cognitive_qa_report.json"),
            trace_path=str(trace_path),
            certificate_ids=[c.certificate_id for c in analysis.certificates],
            p6_summary=summary,
        )

    def _try_cache(self, run_plan: RunPlan) -> RunExecutionRecord | None:
        run_dir = Path(run_plan.artifact_path)
        summary_path = run_dir / "cognitive_qa_report.json"
        if not summary_path.exists():
            return None
        summary = json.loads(summary_path.read_text(encoding="utf-8")).get("summary") or {}
        return RunExecutionRecord(
            plan=run_plan,
            status=RunStatus.COMPLETED,
            attempts=0,
            summary_path=str(summary_path),
            trace_path=str(run_dir / "raw_trace.json"),
            certificate_ids=list(summary.get("certificate_ids") or []),
            p6_summary=summary,
        )
