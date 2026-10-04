"""CRS — Cognitive Recovery Score v1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nexo_qa.failures.episodes import FailureEpisode
from nexo_qa.metrics.models import MetricResult

CRS_VERSION = "crs_v1"


@dataclass
class CRSResult:
    version: str = CRS_VERSION
    value: float | None = None
    recovered_episodes: int = 0
    total_episodes: int = 0
    disclaimer: str = "simulation-derived; not human-calibrated"

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "value": None if self.value is None else round(self.value, 2),
            "recovered_episodes": self.recovered_episodes,
            "total_episodes": self.total_episodes,
            "disclaimer": self.disclaimer,
        }


def compute_crs(episodes: list[FailureEpisode]) -> CRSResult:
    if not episodes:
        return CRSResult(value=None, total_episodes=0, recovered_episodes=0)
    recovered = sum(1 for ep in episodes if ep.recovered)
    base = recovered / len(episodes)
    cost_penalty = sum((ep.end_tick - ep.start_tick) for ep in episodes) / max(1, len(episodes) * 10)
    value = max(0.0, min(100.0, (base * (1.0 - min(0.5, cost_penalty))) * 100.0))
    return CRSResult(value=value, recovered_episodes=recovered, total_episodes=len(episodes))


def crs_metric_result(crs: CRSResult) -> MetricResult:
    return MetricResult(
        metric_id="crs_v1",
        value=crs.value,
        status="AVAILABLE" if crs.value is not None else "NOT_AVAILABLE",
        coverage=1.0 if crs.total_episodes else 0.0,
        version=CRS_VERSION,
        metadata=crs.to_dict(),
    )
