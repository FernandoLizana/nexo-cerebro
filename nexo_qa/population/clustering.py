"""Deterministic failure clustering across population runs."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from nexo_qa.population.models import RunExecutionRecord, RunStatus


@dataclass
class PopulationFailureCluster:
    cluster_id: str
    family: str
    failure_type: str
    occurrence_count: int = 0
    affected_run_count: int = 0
    affected_cohorts: list[str] = field(default_factory=list)
    severity_distribution: dict[str, int] = field(default_factory=dict)
    certificate_refs: list[str] = field(default_factory=list)
    affected_run_ids: list[str] = field(default_factory=list)
    simulation_prevalence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "family": self.family,
            "failure_type": self.failure_type,
            "occurrence_count": self.occurrence_count,
            "affected_run_count": self.affected_run_count,
            "affected_cohorts": list(self.affected_cohorts),
            "severity_distribution": dict(self.severity_distribution),
            "certificate_refs": list(self.certificate_refs),
            "affected_run_ids": list(self.affected_run_ids),
            "simulation_prevalence": round(self.simulation_prevalence, 4),
        }


def cluster_key(family: str, failure_type: str) -> str:
    return f"{family}::{failure_type}"


class FailureClusterer:
    def cluster(self, records: list[RunExecutionRecord]) -> list[PopulationFailureCluster]:
        buckets: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "family": "",
                "failure_type": "",
                "occurrence_count": 0,
                "run_ids": set(),
                "cohorts": set(),
                "severity": defaultdict(int),
                "certificates": [],
            }
        )
        valid_runs = sum(1 for r in records if r.status == RunStatus.COMPLETED)
        for rec in records:
            if rec.status != RunStatus.COMPLETED or not rec.p6_summary:
                continue
            for issue in rec.p6_summary.get("top_issues") or []:
                family = str(issue.get("failure_family", "UNKNOWN"))
                for ft in issue.get("failure_types") or ["UNCLASSIFIED_FAILURE"]:
                    key = cluster_key(family, ft)
                    b = buckets[key]
                    b["family"] = family
                    b["failure_type"] = ft
                    b["occurrence_count"] += int(issue.get("occurrences", 1))
                    b["run_ids"].add(rec.plan.run_id)
                    b["cohorts"].add(rec.plan.cohort_id)
                    sev = str(issue.get("severity", "INFO"))
                    b["severity"][sev] += 1
                    for cid in issue.get("certificate_ids") or rec.certificate_ids:
                        if cid and cid not in b["certificates"]:
                            b["certificates"].append(cid)
            # Rare critical from certificates in summary failures
            for cert_id in rec.certificate_ids:
                pass

        clusters: list[PopulationFailureCluster] = []
        for i, (key, b) in enumerate(sorted(buckets.items()), start=1):
            run_ids = sorted(b["run_ids"])
            prev = len(run_ids) / max(1, valid_runs)
            clusters.append(
                PopulationFailureCluster(
                    cluster_id=f"cluster-{i:03d}",
                    family=b["family"],
                    failure_type=b["failure_type"],
                    occurrence_count=b["occurrence_count"],
                    affected_run_count=len(run_ids),
                    affected_cohorts=sorted(b["cohorts"]),
                    severity_distribution=dict(b["severity"]),
                    certificate_refs=b["certificates"][:10],
                    affected_run_ids=run_ids,
                    simulation_prevalence=prev,
                )
            )
        clusters.sort(key=lambda c: (c.severity_distribution.get("CRITICAL", 0), c.simulation_prevalence), reverse=True)
        return clusters

    def rare_critical(self, clusters: list[PopulationFailureCluster]) -> list[dict[str, Any]]:
        rare: list[dict[str, Any]] = []
        for c in clusters:
            if c.severity_distribution.get("CRITICAL") or c.severity_distribution.get("HIGH"):
                rare.append(c.to_dict())
        return rare
