"""Metric registry — versioned definitions."""

from __future__ import annotations

from nexo_qa.metrics.models import MetricDefinition

METRICS_VERSION = "metrics-v1"

METRIC_REGISTRY: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        metric_id="task_completion",
        name="Task Completion",
        version=METRICS_VERSION,
        scope="run",
        range_min=0.0,
        range_max=1.0,
        units="boolean",
        formula="1 if final progress level == complete else 0",
        required_inputs=("final_progress",),
        interpretation="Whether declarative goal reached complete progress",
        limitations="Uses progress evaluator, not oracle path",
    ),
    MetricDefinition(
        metric_id="action_count",
        name="Action Count",
        version=METRICS_VERSION,
        scope="run",
        range_min=0.0,
        range_max=10000.0,
        units="count",
        formula="len(action_history)",
        required_inputs=("action_history",),
        interpretation="Total actions executed",
        limitations="Descriptive",
    ),
    MetricDefinition(
        metric_id="repeated_action_rate",
        name="Repeated Action Rate",
        version=METRICS_VERSION,
        scope="run",
        range_min=0.0,
        range_max=1.0,
        units="ratio",
        formula="repeated_pairs / max(1, len(actions)-1)",
        required_inputs=("action_history",),
        interpretation="Fraction of consecutive duplicate actions",
        limitations="simulation-derived",
    ),
    MetricDefinition(
        metric_id="ncfs_v1",
        name="NEXO Cognitive Friction Score",
        version="ncfs_v1",
        scope="run",
        range_min=0.0,
        range_max=100.0,
        units="score",
        formula="weighted sum of friction components, normalized 0-100",
        required_inputs=("failures", "core_metrics"),
        interpretation="Engineering friction proxy — not human UX score",
        limitations="simulation-derived; not human-calibrated",
    ),
    MetricDefinition(
        metric_id="ehfp_v1",
        name="NEXO Estimated Human Failure Proxy",
        version="ehfp_v1",
        scope="run",
        range_min=0.0,
        range_max=100.0,
        units="score",
        formula="terminal failure + severity + stagnation proxy",
        required_inputs=("failures", "progress"),
        interpretation="Failure propensity proxy — NOT a probability",
        limitations="EHFP IS NOT A PROBABILITY IN P6",
    ),
    MetricDefinition(
        metric_id="crs_v1",
        name="Cognitive Recovery Score",
        version="crs_v1",
        scope="run",
        range_min=0.0,
        range_max=100.0,
        units="score",
        formula="recovery success weighted by cost",
        required_inputs=("failure_episodes",),
        interpretation="Simulated recovery quality",
        limitations="simulation-derived",
    ),
)


def get_metric(metric_id: str) -> MetricDefinition | None:
    for m in METRIC_REGISTRY:
        if m.metric_id == metric_id:
            return m
    return None
