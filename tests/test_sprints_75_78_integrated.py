"""Tests Sprints 75–78 — Fase 15 (agency audit + science bundle)."""

from __future__ import annotations

from nexo.behavioral.agency_audit import summarize_agency_audit
from nexo.behavioral.causal_certificate import build_causal_certificate, summarize_causal_certificates
from nexo.behavioral.science_bundle import export_science_bundle
from nexo.behavioral.task_registry import TASK_REGISTRY
from nexo.behavioral.tasks import (
    run_agency_audit_smoke_task,
    run_causal_certificate_smoke_task,
    run_science_bundle_smoke_task,
)
from nexo.integrated_runtime import _repo_root, runtime_from_config


def test_integrated_v90_yaml():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v90.yaml")
    assert rt.config.profile == "integrated_v90"
    assert rt.config.agency_audit_mode == "integrated"
    assert rt.config.science_bundle_mode == "integrated"
    assert rt.config.causal_certificate_mode == "integrated"


def test_causal_certificate_v2_after_motor():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v90.yaml")
    rt.config.ticks = 12
    rt.run()
    summary = summarize_causal_certificates(rt)
    assert summary["certificate_events"] >= 12
    assert summary["valid_certificates"] >= 1
    assert summary["agency_valid_certificates"] >= 1
    cert = build_causal_certificate(rt)
    assert cert.get("action_source") in ("integrated", "legacy", "unified_motor", "none")


def test_agency_audit_summary():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v90.yaml")
    rt.config.ticks = 16
    rt.run()
    summary = summarize_agency_audit(rt)
    assert summary["audit_mode"] == "causal_certificate_v2"
    assert summary["agency_score"] >= 0.0


def test_science_bundle_export(tmp_path):
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v90.yaml")
    rt.config.ticks = 8
    result = rt.run()
    out = tmp_path / "bundle.json"
    exported = export_science_bundle(rt, result, out, repo_root=_repo_root())
    assert exported["exported"] is True
    assert exported["science_bundle"] is True


def test_task_registry_fase15():
    for tid in ("agency_audit_smoke", "science_bundle_smoke"):
        assert tid in TASK_REGISTRY


def test_agency_audit_smoke_task():
    result = run_agency_audit_smoke_task(seed=42, ticks=24)
    assert result.task_id == "agency_audit_smoke"
    assert result.primary_metrics["agency_score"] >= 0.0


def test_causal_certificate_smoke_v90():
    result = run_causal_certificate_smoke_task(seed=42, ticks=20)
    assert result.primary_metrics["valid_certificates"] >= 0.0


def test_science_bundle_smoke_task():
    result = run_science_bundle_smoke_task(seed=42, ticks=16)
    assert result.task_id == "science_bundle_smoke"
    assert result.primary_metrics["science_bundle"] == 1.0
