"""Core Cognitive QA metrics."""

from __future__ import annotations

from collections import Counter
from typing import Any

from nexo_qa.analysis.models import RawRunTrace
from nexo_qa.failures.episodes import FailureEpisode
from nexo_qa.failures.taxonomy import CognitiveFailure, CognitiveFailureType
from nexo_qa.metrics.models import MetricResult


def compute_core_metrics(
    raw: RawRunTrace,
    failures: list[CognitiveFailure],
    episodes: list[FailureEpisode],
) -> dict[str, MetricResult]:
    meta = raw.metadata
    actions = list(meta.get("action_history") or [])
    progress = meta.get("final_progress") or {}
    level = str(progress.get("level", "unknown"))

    results: dict[str, MetricResult] = {}

    task_complete = 1.0 if level == "complete" else 0.0
    results["task_completion"] = MetricResult(
        metric_id="task_completion",
        value=task_complete,
        status="AVAILABLE",
        coverage=1.0 if progress else 0.0,
        evidence_refs=(raw.run_id,),
    )

    results["action_count"] = MetricResult(
        metric_id="action_count",
        value=float(len(actions)),
        status="AVAILABLE" if actions is not None else "NOT_AVAILABLE",
        coverage=1.0,
    )

    repeated = sum(1 for i in range(1, len(actions)) if actions[i] == actions[i - 1])
    rate = repeated / max(1, len(actions) - 1) if len(actions) > 1 else 0.0
    results["repeated_action_rate"] = MetricResult(
        metric_id="repeated_action_rate",
        value=rate,
        status="AVAILABLE" if actions else "NOT_AVAILABLE",
        coverage=1.0 if len(actions) > 1 else 0.5,
    )

    stagnation_ticks = sum(1 for f in failures if f.failure_type == CognitiveFailureType.NO_PROGRESS)
    results["no_progress_duration"] = MetricResult(
        metric_id="no_progress_duration",
        value=float(stagnation_ticks),
        status="AVAILABLE" if failures else "PARTIAL",
        coverage=0.8 if failures else 0.0,
    )

    loop_count = sum(1 for f in failures if f.failure_type == CognitiveFailureType.NAVIGATION_LOOP)
    results["navigation_loop_count"] = MetricResult(
        metric_id="navigation_loop_count",
        value=float(loop_count),
        status="AVAILABLE",
        coverage=1.0,
    )

    percept_miss = sum(1 for f in failures if f.family.value == "PERCEPTION")
    results["perceptual_miss_count"] = MetricResult(
        metric_id="perceptual_miss_count",
        value=float(percept_miss),
        status="AVAILABLE",
        coverage=1.0 if failures else 0.0,
    )

    attn_miss = sum(
        1 for f in failures
        if f.failure_type in (CognitiveFailureType.TARGET_VISIBLE_NOT_ATTENDED, CognitiveFailureType.DISTRACTOR_CAPTURE)
    )
    results["attention_miss_count"] = MetricResult(
        metric_id="attention_miss_count",
        value=float(attn_miss),
        status="AVAILABLE",
        coverage=1.0 if failures else 0.0,
    )

    mem_fail = sum(1 for f in failures if f.family.value == "MEMORY")
    results["memory_failure_count"] = MetricResult(
        metric_id="memory_failure_count",
        value=float(mem_fail),
        status="AVAILABLE" if mem_fail or raw.ticks > 0 else "NOT_AVAILABLE",
        coverage=1.0 if any(ev.get("event_type") == "working_memory.updated" for ev in raw.events) else 0.0,
    )

    recoverable = [ep for ep in episodes if ep.recovered or any(f.recoverable for f in ep.failures)]
    recovered = [ep for ep in episodes if ep.recovered]
    rr = len(recovered) / max(1, len(recoverable)) if recoverable else None
    results["recovery_success_rate"] = MetricResult(
        metric_id="recovery_success_rate",
        value=rr,
        status="AVAILABLE" if recoverable else "NOT_AVAILABLE",
        coverage=len(recovered) / max(1, len(episodes)) if episodes else 0.0,
    )

    first_attempt = task_complete == 1.0 and not any(
        f.severity in ("HIGH", "CRITICAL") for f in failures
    )
    results["first_attempt_success"] = MetricResult(
        metric_id="first_attempt_success",
        value=1.0 if first_attempt else 0.0,
        status="AVAILABLE" if progress else "PARTIAL",
        coverage=0.9,
    )

    return results
