"""P9 Human Calibration Lab tests."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import nexo_qa
import yaml

from nexo_qa.human_lab.alignment import BehavioralAlignmentAnalyzer
from nexo_qa.human_lab.calibration.domain import block_hfp_claim, evaluate_domain_scope, ood_policy_manifest
from nexo_qa.human_lab.calibration.ehfp_hfp import calibrate_ehfp_to_hfp, hfp_claim_allowed
from nexo_qa.human_lab.calibration.engine import CalibrationEngine
from nexo_qa.human_lab.calibration.crs_validation import validate_crs_against_human
from nexo_qa.human_lab.calibration.ncfs_validation import validate_ncfs_against_human
from nexo_qa.human_lab.calibration.registry import CalibrationRegistry
from nexo_qa.human_lab.cards import build_data_card, build_model_card
from nexo_qa.human_lab.certificate_review import review_certificate
from nexo_qa.human_lab.dataset import build_dataset_from_study, write_dataset_manifest
from nexo_qa.human_lab.events import normalize_events, normalize_human_event
from nexo_qa.human_lab.hbc import compute_hbc_from_summaries
from nexo_qa.human_lab.matched import verify_task_version_match
from nexo_qa.human_lab.models import CalibrationDomain, HumanRunSummary, HumanStudySpec
from nexo_qa.human_lab.path_similarity import normalized_levenshtein_similarity
from nexo_qa.human_lab.perturbation_alignment import perturbation_alignment
from nexo_qa.human_lab.privacy import delete_participant, pseudonymize_participant_id, redact_secrets
from nexo_qa.human_lab.reporting import build_calibration_report, build_calibration_report_markdown
from nexo_qa.human_lab.split import grouped_train_holdout_split, leave_one_participant_out
from nexo_qa.human_lab.statistics import brier_score, expected_calibration_error
from nexo_qa.human_lab.synthetic import load_synthetic_nexo_summaries, load_synthetic_runs, synthetic_disclaimer
from nexo_qa.human_lab.taxonomy_validation import taxonomy_metrics
from nexo_qa.human_lab.validation import validate_study_spec

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "configs" / "nexo_qa" / "human_lab" / "pilot_study.yaml"


def _study() -> HumanStudySpec:
    return HumanStudySpec.from_dict(yaml.safe_load(CONFIG.read_text(encoding="utf-8")))


def test_p9_phase_version() -> None:
    assert nexo_qa.__phase__ == "P9"


def test_study_spec_validation() -> None:
    spec = _study()
    assert not validate_study_spec(spec)


def test_human_nexo_task_version_match() -> None:
    run = HumanRunSummary(
        human_run_id="hr-1",
        participant_id="p-1",
        task_id="web_form_task",
        task_version="1",
        environment_version="web_lab_v1",
        condition="BASELINE",
    )
    ok, issues = verify_task_version_match(run, {"task_id": "web_form_task", "task_version": "1", "environment_version": "web_lab_v1"})
    assert ok and not issues


def test_human_event_normalization() -> None:
    events = normalize_events(
        [{"participant_id": "p", "human_run_id": "h", "task_id": "t", "event_id": "1", "timestamp_ms": 0, "event_type": "click", "semantic_target": "btn"}]
    )
    assert events[0].action_category == "ACTIVATE"


def test_pseudonymization() -> None:
    a = pseudonymize_participant_id("alice", study_salt="salt")
    b = pseudonymize_participant_id("alice", study_salt="salt")
    assert a == b and a.startswith("participant-")


def test_secret_redaction() -> None:
    assert "[REDACTED]" in redact_secrets("password: hunter2")
    evt = normalize_human_event(
        {
            "participant_id": "p",
            "human_run_id": "h",
            "task_id": "t",
            "event_id": "1",
            "timestamp_ms": 0,
            "event_type": "type",
            "metadata": {"css_selector": "#x"},
        }
    )
    assert "css_selector" not in evt.metadata


def test_delete_participant(tmp_path: Path) -> None:
    run_file = tmp_path / "human_runs" / "r.json"
    run_file.parent.mkdir(parents=True)
    run_file.write_text(json.dumps({"participant_id": "p-del", "human_run_id": "hr"}), encoding="utf-8")
    result = delete_participant("p-del", tmp_path)
    assert result["deleted"] is True


def test_dataset_versioning(tmp_path: Path) -> None:
    spec = _study()
    ds = build_dataset_from_study(spec, dataset_id="ds-test", raw_runs=load_synthetic_runs(), human_data_status="NO_HUMAN_DATA")
    path = write_dataset_manifest(ds, tmp_path / "dataset_manifest.json")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["manifest_hash"] == ds.manifest_hash()


def test_train_holdout_split() -> None:
    split = grouped_train_holdout_split(["p1", "p2", "p3", "p4", "p5", "p6"], holdout_fraction=0.2)
    assert not set(split["train"]) & set(split["holdout"])


def test_grouped_split_by_participant() -> None:
    folds = leave_one_participant_out(["p1", "p2", "p3"])
    assert len(folds) == 3


def test_path_similarity() -> None:
    sim = normalized_levenshtein_similarity(["ACTIVATE", "TYPE"], ["ACTIVATE", "SELECT"])
    assert 0.0 <= sim <= 1.0


def test_hbc_components() -> None:
    human = load_synthetic_runs()
    nexo = load_synthetic_nexo_summaries()
    hbc = compute_hbc_from_summaries(human, nexo, synthetic=True)
    assert hbc.disclaimer.startswith("SYNTHETIC")
    assert hbc.hbc_outcome is not None


def test_ncfs_validation_pipeline() -> None:
    result = validate_ncfs_against_human(load_synthetic_runs(), load_synthetic_nexo_summaries(), synthetic=True)
    assert result["ncfs_version"] == "ncfs_v1"


def test_crs_validation_pipeline() -> None:
    result = validate_crs_against_human(load_synthetic_runs(), load_synthetic_nexo_summaries(), synthetic=True)
    assert result["crs_version"] == "crs_v1"


def test_ehfp_calibration_pipeline() -> None:
    result = calibrate_ehfp_to_hfp([0.2, 0.8, 0.5], [0, 1, 0], calibration_id="c1", domain_id="d1")
    assert result["ehfp_version"] == "ehfp_v1"


def test_hfp_claim_block_when_not_validated() -> None:
    allowed, reason = hfp_claim_allowed(
        human_data_status="NO_HUMAN_DATA",
        calibration_status="EXPERIMENTAL",
        domain_scope="CALIBRATED",
        holdout_evaluated=False,
    )
    assert allowed is False
    assert "NO_HUMAN_DATA" in reason or "holdout" in reason or "EXPERIMENTAL" in reason


def test_ood_block() -> None:
    domain = CalibrationDomain(domain_id="web_lab", task_families=("web_form_task",))
    scope = evaluate_domain_scope(domain, task_id="unknown_task", condition="BASELINE")
    allowed, _ = block_hfp_claim(scope, calibration_validated=True)
    assert scope == "OUT_OF_DOMAIN"
    assert allowed is False


def test_calibration_curve() -> None:
    result = calibrate_ehfp_to_hfp([0.1, 0.5, 0.9], [0, 0, 1], calibration_id="c", domain_id="d")
    assert isinstance(result["calibration_curve"], list)


def test_brier_score() -> None:
    assert brier_score([0.2, 0.8], [0, 1]) == 0.04


def test_failure_taxonomy_confusion_matrix() -> None:
    metrics = taxonomy_metrics(["A", "A", "B"], ["A", "B", "B"])
    assert metrics["f1"] is not None


def test_certificate_review_pipeline() -> None:
    review = review_certificate(
        {"certificate_id": "c1", "failure": {"failure_type": "X", "causal_relation": "associated_with"}, "evidence": [{"tick": 1}]}
    )
    assert review["evidence_ok"] is True


def test_perturbation_alignment() -> None:
    result = perturbation_alignment(
        [{"completion_delta": -0.1, "action_delta": 2}],
        [{"completion_delta": -0.2, "action_delta": 3}],
        synthetic=True,
    )
    assert result["synthetic"] is True


def test_calibration_registry() -> None:
    from nexo_qa.human_lab.models import CalibrationRecord

    reg = CalibrationRegistry()
    reg.register(CalibrationRecord(calibration_id="cal-1", dataset_id="ds-1", domain_id="dom"))
    assert reg.get("cal-1") is not None


def test_model_card() -> None:
    from nexo_qa.human_lab.models import CalibrationRecord

    card = build_model_card(CalibrationRecord(calibration_id="cal-1"), synthetic=True)
    assert "SYNTHETIC" in card


def test_data_card() -> None:
    spec = _study()
    ds = build_dataset_from_study(spec, dataset_id="ds", raw_runs=load_synthetic_runs())
    card = build_data_card(ds)
    assert "SYNTHETIC" in card


def test_synthetic_label_no_fake_validation() -> None:
    d = synthetic_disclaimer()
    assert "NOT HUMAN VALIDATION" in d["warning"]


def test_calibration_engine_synthetic(tmp_path: Path) -> None:
    spec = _study()
    ds = build_dataset_from_study(spec, dataset_id="ds-syn", raw_runs=load_synthetic_runs())
    domain = CalibrationDomain(domain_id="web_lab_v1", task_families=("web_form_task",))
    engine = CalibrationEngine()
    result = engine.fit_and_validate(
        dataset=ds,
        domain=domain,
        human_summaries=load_synthetic_runs(),
        nexo_summaries=load_synthetic_nexo_summaries(),
        synthetic=True,
    )
    assert result["synthetic"] is True
    assert result["hfp_claim_allowed"] is False
    report = build_calibration_report(
        human_data_status="NO_HUMAN_DATA",
        study_id=spec.study_id,
        dataset_id=ds.dataset_id,
        calibration_result=result,
        hfp_claim_allowed=False,
        synthetic=True,
    )
    assert "CONDITIONAL PASS" in report["final_verdict"]


def test_chaos_report_markdown_disclaimer() -> None:
    report = build_calibration_report(
        human_data_status="NO_HUMAN_DATA",
        study_id="s",
        dataset_id="d",
        calibration_result={},
        hfp_claim_allowed=False,
        synthetic=True,
    )
    md = build_calibration_report_markdown(report)
    assert "Human data status" in md


def test_ece_metric() -> None:
    assert expected_calibration_error([0.1, 0.9], [0, 1]) is not None


def test_full_regression_p0_p8() -> None:
    from nexo_qa.chaos import PerturbationSpec
    from nexo_qa.population import PopulationSpec

    assert nexo_qa.__phase__ == "P9"
    assert PopulationSpec is not None
    assert PerturbationSpec is not None
    assert ood_policy_manifest()["out_of_domain_behavior"] == "HFP=NOT_AVAILABLE"


def test_behavioral_alignment_analyzer() -> None:
    alignment = BehavioralAlignmentAnalyzer().analyze(
        human_summaries=load_synthetic_runs(),
        nexo_summaries=load_synthetic_nexo_summaries(),
    )
    assert alignment.n_pairs > 0
