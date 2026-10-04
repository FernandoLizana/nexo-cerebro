"""Population aggregation — distributions, cohort results, comparisons."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any

from nexo_qa.population.models import RunExecutionRecord, RunStatus


@dataclass
class DistributionStats:
    count: int
    mean: float | None = None
    median: float | None = None
    std: float | None = None
    min: float | None = None
    max: float | None = None
    p10: float | None = None
    p25: float | None = None
    p50: float | None = None
    p75: float | None = None
    p90: float | None = None
    status: str = "AVAILABLE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "mean": self._r(self.mean),
            "median": self._r(self.median),
            "std": self._r(self.std),
            "min": self._r(self.min),
            "max": self._r(self.max),
            "p10": self._r(self.p10),
            "p25": self._r(self.p25),
            "p50": self._r(self.p50),
            "p75": self._r(self.p75),
            "p90": self._r(self.p90),
            "status": self.status,
        }

    @staticmethod
    def _r(v: float | None) -> float | None:
        return None if v is None else round(v, 4)


def compute_distribution(values: list[float]) -> DistributionStats:
    n = len(values)
    if n == 0:
        return DistributionStats(count=0, status="NOT_AVAILABLE")
    if n < 5:
        return DistributionStats(
            count=n,
            mean=statistics.mean(values),
            median=statistics.median(values),
            min=min(values),
            max=max(values),
            status="INSUFFICIENT_SAMPLE",
        )
    ordered = sorted(values)
    return DistributionStats(
        count=n,
        mean=statistics.mean(values),
        median=statistics.median(values),
        std=statistics.pstdev(values) if n > 1 else 0.0,
        min=min(values),
        max=max(values),
        p10=_percentile(ordered, 0.10),
        p25=_percentile(ordered, 0.25),
        p50=_percentile(ordered, 0.50),
        p75=_percentile(ordered, 0.75),
        p90=_percentile(ordered, 0.90),
        status="AVAILABLE",
    )


def _percentile(ordered: list[float], p: float) -> float:
    if not ordered:
        return 0.0
    idx = min(len(ordered) - 1, max(0, int(p * (len(ordered) - 1))))
    return ordered[idx]


def _valid_cognitive(rec: RunExecutionRecord) -> bool:
    return rec.status == RunStatus.COMPLETED and rec.p6_summary is not None


@dataclass
class CohortResult:
    cohort_id: str
    n_planned: int = 0
    n_completed: int = 0
    n_valid: int = 0
    n_infra_failed: int = 0
    completion_counts: dict[str, int] = field(default_factory=dict)
    metric_distributions: dict[str, dict[str, Any]] = field(default_factory=dict)
    failure_frequency: dict[str, int] = field(default_factory=dict)
    run_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cohort_id": self.cohort_id,
            "n_planned": self.n_planned,
            "n_completed": self.n_completed,
            "n_valid": self.n_valid,
            "n_infra_failed": self.n_infra_failed,
            "valid_runs_denominator": self.n_valid,
            "completion_counts": dict(self.completion_counts),
            "metric_distributions": self.metric_distributions,
            "failure_frequency": self.failure_frequency,
            "run_ids": list(self.run_ids),
        }


@dataclass
class PopulationResult:
    population_id: str
    spec_hash: str
    planned_runs: int
    completed_runs: int
    infrastructure_failures: int
    task_failures: int
    valid_runs: int
    cohorts: dict[str, CohortResult] = field(default_factory=dict)
    aggregate_metrics: dict[str, Any] = field(default_factory=dict)
    failure_clusters: list[dict[str, Any]] = field(default_factory=list)
    cohort_comparisons: list[dict[str, Any]] = field(default_factory=list)
    versions: dict[str, str] = field(default_factory=dict)
    coverage: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "population_id": self.population_id,
            "spec_hash": self.spec_hash,
            "planned_runs": self.planned_runs,
            "completed_runs": self.completed_runs,
            "infrastructure_failures": self.infrastructure_failures,
            "task_failures": self.task_failures,
            "valid_runs": self.valid_runs,
            "cohorts": {k: v.to_dict() for k, v in self.cohorts.items()},
            "aggregate_metrics": self.aggregate_metrics,
            "failure_clusters": self.failure_clusters,
            "cohort_comparisons": self.cohort_comparisons,
            "versions": self.versions,
            "coverage": self.coverage,
            "disclaimer": "simulation distribution — not human population behavior",
        }


class PopulationAggregator:
    def aggregate(
        self,
        *,
        population_id: str,
        spec_hash: str,
        records: list[RunExecutionRecord],
        clusters: list[dict[str, Any]] | None = None,
        versions: dict[str, str] | None = None,
    ) -> PopulationResult:
        by_cohort: dict[str, list[RunExecutionRecord]] = {}
        for rec in records:
            by_cohort.setdefault(rec.plan.cohort_id, []).append(rec)

        cohort_results: dict[str, CohortResult] = {}
        all_ncfs: list[float] = []
        all_valid: list[RunExecutionRecord] = []

        for cohort_id, cohort_recs in by_cohort.items():
            cr = CohortResult(cohort_id=cohort_id, n_planned=len(cohort_recs))
            ncfs_vals: list[float] = []
            crs_vals: list[float] = []
            ehfp_vals: list[float] = []
            for rec in cohort_recs:
                cr.run_ids.append(rec.plan.run_id)
                if rec.status == RunStatus.COMPLETED:
                    cr.n_completed += 1
                if rec.status == RunStatus.FAILED_INFRASTRUCTURE:
                    cr.n_infra_failed += 1
                if not _valid_cognitive(rec):
                    continue
                cr.n_valid += 1
                all_valid.append(rec)
                summary = rec.p6_summary or {}
                status = str(summary.get("assessment_status", "unknown"))
                cr.completion_counts[status] = cr.completion_counts.get(status, 0) + 1
                ncfs = (summary.get("ncfs") or {}).get("value")
                if ncfs is not None:
                    ncfs_vals.append(float(ncfs))
                    all_ncfs.append(float(ncfs))
                crs = (summary.get("crs") or {}).get("value")
                if crs is not None:
                    crs_vals.append(float(crs))
                ehfp = (summary.get("ehfp") or {}).get("value")
                if ehfp is not None:
                    ehfp_vals.append(float(ehfp))
                for issue in summary.get("top_issues") or []:
                    for ft in issue.get("failure_types") or []:
                        cr.failure_frequency[ft] = cr.failure_frequency.get(ft, 0) + 1
            cr.metric_distributions = {
                "ncfs_v1": compute_distribution(ncfs_vals).to_dict(),
                "crs_v1": compute_distribution(crs_vals).to_dict(),
                "ehfp_v1": compute_distribution(ehfp_vals).to_dict(),
            }
            cohort_results[cohort_id] = cr

        comparisons = self._cohort_comparisons(cohort_results)
        infra = sum(1 for r in records if r.status == RunStatus.FAILED_INFRASTRUCTURE)
        task_fail = sum(1 for r in records if r.status == RunStatus.FAILED_TASK)
        completed = sum(1 for r in records if r.status == RunStatus.COMPLETED)

        return PopulationResult(
            population_id=population_id,
            spec_hash=spec_hash,
            planned_runs=len(records),
            completed_runs=completed,
            infrastructure_failures=infra,
            task_failures=task_fail,
            valid_runs=len(all_valid),
            cohorts=cohort_results,
            aggregate_metrics={"ncfs_v1": compute_distribution(all_ncfs).to_dict()},
            failure_clusters=clusters or [],
            cohort_comparisons=comparisons,
            versions=versions or {},
            coverage={
                "planned": len(records),
                "completed": completed,
                "valid_cognitive_runs": len(all_valid),
                "infra_failures": infra,
            },
        )

    def _cohort_comparisons(self, cohorts: dict[str, CohortResult]) -> list[dict[str, Any]]:
        ids = sorted(cohorts.keys())
        out: list[dict[str, Any]] = []
        if len(ids) < 2:
            return out
        base = cohorts.get("baseline") or cohorts[ids[0]]
        for cid in ids[1:]:
            other = cohorts[cid]
            base_ncfs = (base.metric_distributions.get("ncfs_v1") or {}).get("median")
            other_ncfs = (other.metric_distributions.get("ncfs_v1") or {}).get("median")
            delta = None
            if base_ncfs is not None and other_ncfs is not None:
                delta = round(float(other_ncfs) - float(base_ncfs), 2)
            out.append(
                {
                    "cohort_a": base.cohort_id,
                    "cohort_b": cid,
                    "ncfs_median_delta": delta,
                    "valid_runs_a": base.n_valid,
                    "valid_runs_b": other.n_valid,
                }
            )
        return out
