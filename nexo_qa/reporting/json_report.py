"""JSON cognitive QA report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nexo_qa.analysis.models import RawRunTrace
from nexo_qa.failures.certificate import CognitiveFailureCertificate
from nexo_qa.failures.episodes import FailureEpisode
from nexo_qa.failures.taxonomy import CognitiveFailure
from nexo_qa.metrics.engine import MetricEngineResult
from nexo_qa.reporting.summary import CognitiveQAIssue, CognitiveQARunSummary


def build_json_report(
    *,
    raw: RawRunTrace,
    summary: CognitiveQARunSummary,
    failures: list[CognitiveFailure],
    episodes: list[FailureEpisode],
    certificates: list[CognitiveFailureCertificate],
    issues: list[CognitiveQAIssue],
    metrics: MetricEngineResult,
) -> dict[str, Any]:
    run_dict = raw.to_dict()
    meta = dict(run_dict.get("metadata") or {})
    for key in list(meta.keys()):
        if any(s in key.lower() for s in ("password", "token", "secret")):
            meta[key] = "[REDACTED]"
    run_dict["metadata"] = meta
    return {
        "report_type": "cognitive_qa_report",
        "schema_version": 1,
        "classification_version": "failures-v1",
        "metrics_version": "metrics-v1",
        "run": run_dict,
        "summary": summary.to_dict(),
        "failures": [f.to_dict() for f in failures],
        "episodes": [e.to_dict() for e in episodes],
        "issues": [i.to_dict() for i in issues],
        "certificates": [c.to_dict() for c in certificates],
        "metrics": metrics.to_dict(),
        "disclaimer_en": "These metrics are simulation-derived and are not calibrated estimates of real human behavior.",
        "disclaimer_es": "Estas métricas son derivadas de simulación y no son estimaciones calibradas de conducta humana real.",
    }


def write_json_report(path: Path | str, report: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
