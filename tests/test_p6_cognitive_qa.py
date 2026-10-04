"""P6 Cognitive QA metrics, failures, certificates, reporting."""

from __future__ import annotations

import json
from pathlib import Path

from nexo_qa.analysis import RawRunTrace, analyze_raw_trace, analyze_run_file, normalize_events
from nexo_qa.failures import (
    CLASSIFICATION_VERSION,
    CognitiveFailureType,
    FailureClassifier,
    FailureFamily,
    build_certificate,
    compute_severity,
    merge_failures_into_episodes,
    validate_certificate,
)
from nexo_qa.metrics import METRICS_VERSION
from nexo_qa.metrics.crs import compute_crs
from nexo_qa.metrics.ncfs import compute_ncfs
from nexo_qa.reporting import build_markdown_report

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures" / "cognitive_qa"
FAILURES_PKG = REPO / "nexo_qa" / "failures"


def _load(name: str) -> RawRunTrace:
    return RawRunTrace.from_dict(json.loads((FIXTURES / name).read_text(encoding="utf-8")))


def test_event_normalization() -> None:
    raw = _load("distractor_loop_trace.json")
    events = normalize_events(raw)
    assert len(events) > len(raw.events)
    assert all(e.run_id == raw.run_id for e in events)
    assert not any("data-testid" in json.dumps(e.to_dict()) for e in events)


def test_failure_taxonomy_versioned() -> None:
    assert CLASSIFICATION_VERSION == "failures-v1"
    assert CognitiveFailureType.UNCLASSIFIED_FAILURE.value == "UNCLASSIFIED_FAILURE"
    assert len(FailureFamily) >= 14


def test_perception_failure_classification() -> None:
    raw = _load("distractor_loop_trace.json")
    events = normalize_events(raw)
    result = FailureClassifier().classify(events, raw)
    types = {f.failure_type for f in result.failures}
    assert CognitiveFailureType.DISTRACTOR_CAPTURE in types or CognitiveFailureType.NAVIGATION_LOOP in types


def test_attention_failure_classification() -> None:
    raw = _load("distractor_loop_trace.json")
    events = normalize_events(raw)
    result = FailureClassifier().classify(events, raw)
    assert any(f.family == FailureFamily.ATTENTION for f in result.failures)


def test_memory_failure_classification() -> None:
    raw = _load("distractor_loop_trace.json")
    events = normalize_events(raw)
    result = FailureClassifier().classify(events, raw)
    assert any(f.failure_type == CognitiveFailureType.WORKING_MEMORY_LOSS for f in result.failures)


def test_navigation_loop_detection() -> None:
    raw = _load("distractor_loop_trace.json")
    result = analyze_raw_trace(raw)
    assert any(f.failure_type == CognitiveFailureType.NAVIGATION_LOOP for f in result.failures)


def test_recovery_episode() -> None:
    raw = _load("recovery_success_trace.json")
    result = analyze_raw_trace(raw)
    assert result.summary.assessment_status in ("PASS", "PASS_WITH_FRICTION", "FAIL_RECOVERABLE")


def test_failure_episode_merge() -> None:
    raw = _load("distractor_loop_trace.json")
    events = normalize_events(raw)
    failures = FailureClassifier().classify(events, raw).failures
    episodes = merge_failures_into_episodes(failures)
    assert len(episodes) <= len(failures)


def test_severity_model() -> None:
    sev = compute_severity(goal_impact=0.95, persistence=0.6, terminal_failure=True)
    assert sev.severity in ("HIGH", "CRITICAL")
    assert 0.0 <= sev.severity_score <= 1.0


def test_classification_confidence() -> None:
    raw = _load("distractor_loop_trace.json")
    result = analyze_raw_trace(raw)
    assert all(0.0 <= f.confidence <= 1.0 for f in result.failures)


def test_failure_certificate_generation() -> None:
    raw = _load("distractor_loop_trace.json")
    result = analyze_raw_trace(raw)
    assert result.certificates
    cert = result.certificates[0]
    assert cert.goal.get("description")
    assert cert.persona.get("persona_id")


def test_failure_certificate_refs() -> None:
    raw = _load("distractor_loop_trace.json")
    result = analyze_raw_trace(raw)
    for cert in result.certificates:
        assert cert.evidence
        assert cert.failure.get("failure_id")


def test_failure_certificate_selector_secrecy() -> None:
    raw = _load("distractor_loop_trace.json")
    result = analyze_raw_trace(raw)
    blob = json.dumps([c.to_dict() for c in result.certificates]).lower()
    for token in ("data-testid", "xpath", "playwright", "css selector"):
        assert token not in blob


def test_failure_certificate_secret_redaction() -> None:
    raw = _load("distractor_loop_trace.json")
    raw_meta = dict(raw.metadata)
    raw_meta["password"] = "secret123"
    raw = RawRunTrace(
        run_id=raw.run_id,
        seed=raw.seed,
        ticks=raw.ticks,
        events=raw.events,
        world_trace=raw.world_trace,
        metadata=raw_meta,
    )
    result = analyze_raw_trace(raw)
    blob = json.dumps(result.json_report)
    assert "secret123" not in blob


def test_metric_engine_core_metrics() -> None:
    raw = _load("distractor_loop_trace.json")
    result = analyze_raw_trace(raw)
    assert "action_count" in result.metrics.metrics
    assert result.metrics.metrics["action_count"].status == "AVAILABLE"


def test_ncfs_deterministic() -> None:
    raw = _load("distractor_loop_trace.json")
    r1 = analyze_raw_trace(raw)
    r2 = analyze_raw_trace(raw)
    assert r1.metrics.ncfs == r2.metrics.ncfs


def test_ncfs_partial_coverage() -> None:
    ncfs = compute_ncfs([])
    assert ncfs.coverage == 0.0
    assert ncfs.value is None


def test_ehfp_is_not_probability() -> None:
    raw = _load("distractor_loop_trace.json")
    result = analyze_raw_trace(raw)
    ehfp = result.metrics.ehfp
    assert ehfp.get("is_probability") is False
    assert "propensity" in ehfp.get("label", "").lower()


def test_crs_recovery_difference() -> None:
    ok = analyze_raw_trace(_load("recovery_success_trace.json"))
    bad = analyze_raw_trace(_load("recovery_failure_trace.json"))
    assert (ok.metrics.crs.get("value") or 0) >= (bad.metrics.crs.get("value") or 0)


def test_json_report() -> None:
    raw = _load("distractor_loop_trace.json")
    result = analyze_raw_trace(raw)
    assert result.json_report.get("report_type") == "cognitive_qa_report"
    assert "disclaimer_en" in result.json_report


def test_markdown_report() -> None:
    raw = _load("distractor_loop_trace.json")
    result = analyze_raw_trace(raw)
    md = build_markdown_report(result.json_report)
    assert "Cognitive QA Report" in md
    assert "simulation" in md.lower()


def test_raw_trace_to_report_pipeline() -> None:
    result = analyze_run_file(FIXTURES / "distractor_loop_trace.json")
    assert result.summary
    assert result.json_report
    assert result.failures
    assert result.metrics.ncfs


def test_paired_persona_metric_comparison() -> None:
    a = analyze_raw_trace(_load("distractor_loop_trace.json"))
    b = analyze_raw_trace(_load("recovery_success_trace.json"))
    assert a.metrics.ehfp.get("value") != b.metrics.ehfp.get("value") or a.metrics.ncfs != b.metrics.ncfs


def test_metric_versioning() -> None:
    assert METRICS_VERSION == "metrics-v1"
    raw = _load("distractor_loop_trace.json")
    result = analyze_raw_trace(raw)
    assert result.json_report.get("metrics_version") == "metrics-v1"


def test_classifier_does_not_use_golden_path() -> None:
    text = (FAILURES_PKG / "classifier.py").read_text(encoding="utf-8").lower()
    # Ignore module docstring line when scanning for forbidden runtime tokens
    code = "\n".join(
        line for line in text.splitlines() if not line.strip().startswith('"""') and '"""' not in line[:3]
    )
    for token in ("expected_step", "golden_path", "correct_action"):
        assert token not in code
    assert "if persona" not in code


def test_full_regression_p0_to_p5_imports() -> None:
    import nexo_qa
    from nexo_qa.personas import load_preset

    assert nexo_qa.__phase__ in ("P8", "P9")
    assert load_preset("baseline").persona_id == "baseline"


def test_offline_analyze_no_browser() -> None:
    result = analyze_run_file(FIXTURES / "distractor_loop_trace.json")
    assert result.normalized_event_count > 0
    assert result.json_path is None


def test_certificate_validator() -> None:
    raw = _load("distractor_loop_trace.json")
    events = normalize_events(raw)
    failures = FailureClassifier().classify(events, raw).failures
    cert = build_certificate(raw, failures[0])
    assert not validate_certificate(cert)


def test_analyze_writes_reports(tmp_path: Path) -> None:
    result = analyze_raw_trace(_load("distractor_loop_trace.json"), output_dir=tmp_path)
    assert (tmp_path / "cognitive_qa_report.json").exists()
    assert (tmp_path / "cognitive_qa_report.md").exists()
    assert result.json_path
