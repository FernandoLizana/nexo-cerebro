"""Offline cognitive QA analysis pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from nexo_qa.analysis.capture import capture_run_trace
from nexo_qa.analysis.models import RawRunTrace
from nexo_qa.analysis.normalize import normalize_events
from nexo_qa.failures.certificate import build_certificate, validate_certificate
from nexo_qa.failures.classifier import FailureClassifier
from nexo_qa.failures.episodes import merge_failures_into_episodes
from nexo_qa.metrics.engine import CognitiveQAMetricEngine
from nexo_qa.reporting.json_report import build_json_report, write_json_report
from nexo_qa.reporting.markdown_report import write_markdown_report
from nexo_qa.reporting.summary import aggregate_issues, build_run_summary


@dataclass
class AnalysisResult:
    raw: RawRunTrace
    normalized_event_count: int = 0
    observations: list = field(default_factory=list)
    failures: list = field(default_factory=list)
    episodes: list = field(default_factory=list)
    certificates: list = field(default_factory=list)
    metrics: Any = None
    summary: Any = None
    json_report: dict[str, Any] = field(default_factory=dict)
    markdown_path: str | None = None
    json_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.raw.run_id,
            "normalized_event_count": self.normalized_event_count,
            "failure_count": len(self.failures),
            "episode_count": len(self.episodes),
            "certificate_count": len(self.certificates),
            "summary": self.summary.to_dict() if self.summary else None,
        }


def analyze_raw_trace(
    raw: RawRunTrace,
    *,
    output_dir: Path | str | None = None,
) -> AnalysisResult:
    """Full P6 pipeline: normalize → classify → metrics → certificates → reports."""
    normalized = normalize_events(raw)
    clf = FailureClassifier()
    clf_result = clf.classify(normalized, raw)
    episodes = merge_failures_into_episodes(clf_result.failures)
    engine = CognitiveQAMetricEngine()
    metrics = engine.compute(raw, clf_result.failures, episodes)
    certificates = [build_certificate(raw, f) for f in clf_result.failures[:20]]
    for cert in certificates:
        errs = validate_certificate(cert)
        if errs:
            raise ValueError(f"Certificate validation failed: {errs}")
    issues = aggregate_issues(episodes, certificates)
    meta = raw.metadata
    summary = build_run_summary(
        run_id=raw.run_id,
        persona_id=meta.get("persona_id"),
        goal_description=str(meta.get("goal_description", "")),
        progress_level=str((meta.get("final_progress") or {}).get("level", "unknown")),
        metrics=metrics,
        failures=clf_result.failures,
        episodes=episodes,
        certificates=certificates,
        issues=issues,
    )
    report = build_json_report(
        raw=raw,
        summary=summary,
        failures=clf_result.failures,
        episodes=episodes,
        certificates=certificates,
        issues=issues,
        metrics=metrics,
    )
    result = AnalysisResult(
        raw=raw,
        normalized_event_count=len(normalized),
        observations=clf_result.observations,
        failures=clf_result.failures,
        episodes=episodes,
        certificates=certificates,
        metrics=metrics,
        summary=summary,
        json_report=report,
    )
    if output_dir is not None:
        out = Path(output_dir)
        jp = write_json_report(out / "cognitive_qa_report.json", report)
        mp = write_markdown_report(out / "cognitive_qa_report.md", report)
        result.json_path = str(jp)
        result.markdown_path = str(mp)
    return result


def analyze_run(runtime: Any, *, world: Any | None = None, output_dir: Path | str | None = None) -> AnalysisResult:
    """Capture from live runtime then analyze offline."""
    raw = capture_run_trace(runtime, world=world)
    return analyze_raw_trace(raw, output_dir=output_dir)


def analyze_run_file(path: Path | str, *, output_dir: Path | str | None = None) -> AnalysisResult:
    """Load serialized raw trace JSON and analyze — no browser required."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    raw = RawRunTrace.from_dict(data)
    return analyze_raw_trace(raw, output_dir=output_dir)
