"""Cognitive QA Metric Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nexo_qa.analysis.models import RawRunTrace
from nexo_qa.failures.episodes import FailureEpisode
from nexo_qa.failures.taxonomy import CognitiveFailure
from nexo_qa.metrics.core_metrics import compute_core_metrics
from nexo_qa.metrics.crs import compute_crs, crs_metric_result
from nexo_qa.metrics.ehfp import compute_ehfp, ehfp_metric_result
from nexo_qa.metrics.models import MetricResult
from nexo_qa.metrics.ncfs import compute_ncfs, ncfs_metric_result


@dataclass
class MetricEngineResult:
    metrics: dict[str, MetricResult] = field(default_factory=dict)
    ncfs: dict[str, Any] = field(default_factory=dict)
    ehfp: dict[str, Any] = field(default_factory=dict)
    crs: dict[str, Any] = field(default_factory=dict)
    version: str = "metrics-v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "ncfs": self.ncfs,
            "ehfp": self.ehfp,
            "crs": self.crs,
        }


class CognitiveQAMetricEngine:
    def compute(
        self,
        raw: RawRunTrace,
        failures: list[CognitiveFailure],
        episodes: list[FailureEpisode],
    ) -> MetricEngineResult:
        metrics = compute_core_metrics(raw, failures, episodes)
        ncfs = compute_ncfs(failures)
        ehfp = compute_ehfp(raw, failures, episodes)
        crs = compute_crs(episodes)
        metrics["ncfs_v1"] = ncfs_metric_result(ncfs)
        metrics["ehfp_v1"] = ehfp_metric_result(ehfp)
        metrics["crs_v1"] = crs_metric_result(crs)
        return MetricEngineResult(
            metrics=metrics,
            ncfs=ncfs.to_dict(),
            ehfp=ehfp.to_dict(),
            crs=crs.to_dict(),
        )
