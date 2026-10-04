"""Small persona matrix runner — task × persona × seed (P5 only)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from nexo.behavioral.fingerprint import compute_behavior_fingerprint
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig
from nexo_qa.personas.models import CognitivePersona
from nexo_qa.personas.runtime import apply_persona


@dataclass
class MatrixRunResult:
    persona_id: str
    seed: int
    task_id: str
    actions: tuple[str, ...]
    ticks: int
    frustration_end: float
    fatigue_end: float
    progress_level: str
    errors: int
    fingerprint: dict[str, Any] = field(default_factory=dict)
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "persona": self.persona_id,
            "seed": self.seed,
            "task": self.task_id,
            "actions": list(self.actions),
            "ticks": self.ticks,
            "errors": self.errors,
            "progress": self.progress_level,
            "frustration_end": round(self.frustration_end, 4),
            "fatigue_end": round(self.fatigue_end, 4),
            "fingerprint": self.fingerprint,
            "elapsed_ms": round(self.elapsed_ms, 2),
        }


def run_matrix_cell(
    *,
    task_id: str,
    persona: CognitivePersona,
    seed: int,
    ticks: int,
    setup: Callable[[IntegratedRuntime], Any],
    teardown: Callable[[Any], None] | None = None,
) -> MatrixRunResult:
    """Run one task×persona×seed cell."""
    t0 = time.perf_counter()
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=seed,
            ticks=ticks,
            executive_mode="integrated",
            perception_mode="predictive",
        )
    )
    handle = setup(rt)
    apply_persona(rt, persona, world=rt.scheduler.config.get("world_state"))
    rt.run()
    world = rt.scheduler.config.get("world_state")
    actions = tuple(getattr(world, "action_history", []) or [])
    errors = sum(1 for a in actions if "error" in a.lower())
    pstate = rt.scheduler.config.get("persona_state")
    progress = rt.scheduler.config.get("goal_progress")
    metrics = {
        "survival_success": 1.0 if progress and getattr(progress, "level", "") == "complete" else 0.0,
        "final_energy": float(rt.state_store.state.homeostatic.energy),
        "action_entropy": float(len(set(actions)) / max(1, len(actions))),
        "eat_ratio": 0.0,
        "mean_reward": float(rt.state_store.state.last_reward),
    }
    fp = compute_behavior_fingerprint(metrics, {"trajectory_hash": ""})
    if teardown:
        teardown(handle)
    elif world is not None and hasattr(world, "close"):
        world.close()
    elapsed = (time.perf_counter() - t0) * 1000.0
    return MatrixRunResult(
        persona_id=persona.persona_id,
        seed=seed,
        task_id=task_id,
        actions=actions,
        ticks=ticks,
        frustration_end=float(getattr(pstate, "current_frustration", 0.0)),
        fatigue_end=float(getattr(pstate, "current_fatigue", 0.0)),
        progress_level=str(getattr(progress, "level", "unknown")),
        errors=errors,
        fingerprint=fp,
        elapsed_ms=elapsed,
    )


def run_matrix(
    *,
    task_id: str,
    personas: tuple[CognitivePersona, ...],
    seeds: tuple[int, ...],
    ticks: int,
    setup: Callable[[IntegratedRuntime], Any],
    teardown: Callable[[Any], None] | None = None,
) -> list[MatrixRunResult]:
    results: list[MatrixRunResult] = []
    for persona in personas:
        for seed in seeds:
            results.append(
                run_matrix_cell(
                    task_id=task_id,
                    persona=persona,
                    seed=seed,
                    ticks=ticks,
                    setup=setup,
                    teardown=teardown,
                )
            )
    return results
