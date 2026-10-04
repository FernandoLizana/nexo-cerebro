"""Run summary and issue aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nexo_qa.failures.certificate import CognitiveFailureCertificate
from nexo_qa.failures.episodes import FailureEpisode
from nexo_qa.failures.taxonomy import CognitiveFailure
from nexo_qa.metrics.engine import MetricEngineResult


@dataclass
class CognitiveQAIssue:
    issue_id: str
    title: str
    failure_family: str
    failure_types: list[str]
    severity: str
    occurrences: int
    affected_ticks: tuple[int, ...] = ()
    evidence: list[str] = field(default_factory=list)
    certificate_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "title": self.title,
            "failure_family": self.failure_family,
            "failure_types": self.failure_types,
            "severity": self.severity,
            "occurrences": self.occurrences,
            "affected_ticks": list(self.affected_ticks),
            "evidence": list(self.evidence),
            "certificate_ids": list(self.certificate_ids),
        }


@dataclass
class CognitiveQARunSummary:
    run_id: str
    persona_id: str | None
    goal_description: str
    result: str
    assessment_status: str
    core_metrics: dict[str, Any]
    ncfs: dict[str, Any]
    ehfp: dict[str, Any]
    crs: dict[str, Any]
    failure_count: int
    episode_count: int
    top_issues: list[dict[str, Any]]
    certificate_ids: list[str]
    coverage: dict[str, float]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "persona_id": self.persona_id,
            "goal_description": self.goal_description,
            "result": self.result,
            "assessment_status": self.assessment_status,
            "core_metrics": self.core_metrics,
            "ncfs": self.ncfs,
            "ehfp": self.ehfp,
            "crs": self.crs,
            "failure_count": self.failure_count,
            "episode_count": self.episode_count,
            "top_issues": self.top_issues,
            "certificate_ids": self.certificate_ids,
            "coverage": self.coverage,
            "warnings": list(self.warnings),
            "calibration_disclaimer": "simulation-derived; not human-calibrated",
        }


def aggregate_issues(
    episodes: list[FailureEpisode],
    certificates: list[CognitiveFailureCertificate],
) -> list[CognitiveQAIssue]:
    issues: list[CognitiveQAIssue] = []
    by_family: dict[str, list[FailureEpisode]] = {}
    for ep in episodes:
        by_family.setdefault(ep.family.value, []).append(ep)
    cert_by_fail = {c.failure.get("failure_id"): c.certificate_id for c in certificates}
    for i, (family, eps) in enumerate(sorted(by_family.items()), start=1):
        types: list[str] = []
        for ep in eps:
            types.extend(ep.failure_types)
        types = sorted(set(types))
        sev = max((ep.severity for ep in eps), key=lambda s: ("INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL").index(s))
        cert_ids = [
            cert_by_fail[f.failure_id]
            for ep in eps for f in ep.failures
            if f.failure_id in cert_by_fail
        ]
        issues.append(
            CognitiveQAIssue(
                issue_id=f"issue-{i:03d}",
                title=f"{family} — {types[0] if types else 'unknown'}",
                failure_family=family,
                failure_types=types,
                severity=sev,
                occurrences=sum(len(ep.failures) for ep in eps),
                affected_ticks=tuple(sorted({ep.start_tick for ep in eps})),
                certificate_ids=sorted(set(cert_ids)),
            )
        )
    issues.sort(key=lambda x: ("INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL").index(x.severity), reverse=True)
    return issues


def build_run_summary(
    *,
    run_id: str,
    persona_id: str | None,
    goal_description: str,
    progress_level: str,
    metrics: MetricEngineResult,
    failures: list[CognitiveFailure],
    episodes: list[FailureEpisode],
    certificates: list[CognitiveFailureCertificate],
    issues: list[CognitiveQAIssue],
) -> CognitiveQARunSummary:
    complete = progress_level == "complete"
    has_high = any(f.severity in ("HIGH", "CRITICAL") for f in failures)
    if progress_level == "blocked":
        status = "BLOCKED"
    elif complete and has_high:
        status = "PASS_WITH_FRICTION"
    elif complete:
        status = "PASS"
    elif any(ep.recovered for ep in episodes):
        status = "FAIL_RECOVERABLE"
    elif failures:
        status = "FAIL"
    else:
        status = "PASS"
    core = {
        k: v.to_dict() for k, v in metrics.metrics.items()
        if k not in ("ncfs_v1", "ehfp_v1", "crs_v1")
    }
    ncfs_cov = metrics.ncfs.get("coverage", 0.0)
    return CognitiveQARunSummary(
        run_id=run_id,
        persona_id=persona_id,
        goal_description=goal_description,
        result=progress_level,
        assessment_status=status,
        core_metrics=core,
        ncfs=metrics.ncfs,
        ehfp=metrics.ehfp,
        crs=metrics.crs,
        failure_count=len(failures),
        episode_count=len(episodes),
        top_issues=[i.to_dict() for i in issues[:5]],
        certificate_ids=[c.certificate_id for c in certificates],
        coverage={"ncfs": ncfs_cov, "metrics": 1.0 if metrics.metrics else 0.0},
        warnings=[] if ncfs_cov > 0 else ["NCFS partial coverage — some friction components missing"],
    )
