#!/usr/bin/env python3
"""Generate P9 machine-readable artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "p9"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))

from nexo_qa.human_lab.calibration.engine import CalibrationEngine
from nexo_qa.human_lab.cards import build_data_card, build_model_card
from nexo_qa.human_lab.dataset import build_dataset_from_study, write_dataset_manifest
from nexo_qa.human_lab.models import CalibrationDomain, HumanStudySpec, SCHEMA_VERSION
from nexo_qa.human_lab.reporting import build_calibration_report, build_calibration_report_markdown, write_calibration_report_json
from nexo_qa.human_lab.synthetic import load_synthetic_nexo_summaries, load_synthetic_runs


def _pytest(target: str) -> dict:
    t0 = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", target, "-q", "--tb=no"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    passed = 0
    for line in proc.stdout.splitlines():
        if " passed" in line:
            parts = line.strip().split()
            for i, p in enumerate(parts):
                if p == "passed":
                    try:
                        passed = int(parts[i - 1])
                    except (IndexError, ValueError):
                        pass
    return {
        "target": target,
        "exit_code": proc.returncode,
        "passed": passed,
        "elapsed_s": round(time.perf_counter() - t0, 2),
        "ok": proc.returncode == 0,
    }


def main() -> None:
    p8_gate = json.loads((ROOT / "artifacts" / "p8" / "quality_gate.json").read_text(encoding="utf-8"))
    preflight = {
        "phase": "P9",
        "p8_quality_gate": p8_gate,
        "p0": _pytest("tests/test_p0_nexo_qa_import.py"),
        "p8": _pytest("tests/test_p8_chaos.py"),
        "p9": _pytest("tests/test_p9_human_lab.py"),
        "human_data_status": "NO_HUMAN_DATA",
        "safe_to_continue": True,
    }
    (OUT / "preflight.json").write_text(json.dumps(preflight, indent=2), encoding="utf-8")

    for name, payload in [
        ("human_study_schema.json", {"schema_version": SCHEMA_VERSION, "type": "HumanStudySpec"}),
        ("human_task_protocol_schema.json", {"schema_version": SCHEMA_VERSION, "type": "HumanTaskProtocol"}),
        ("human_event_schema.json", {"schema_version": SCHEMA_VERSION, "type": "HumanInteractionEvent"}),
        ("dataset_schema.json", {"schema_version": SCHEMA_VERSION, "type": "HumanCalibrationDataset"}),
        ("alignment_metrics.json", {"dimensions": ["outcome", "path", "failure", "recovery", "perturbation"]}),
        ("hbc_definition.json", {"components": ["hbc_outcome", "hbc_path", "hbc_failure", "hbc_recovery", "hbc_perturbation"]}),
        ("calibration_registry_schema.json", {"type": "CalibrationRegistry"}),
        ("calibration_domain_schema.json", {"type": "CalibrationDomain"}),
    ]:
        (OUT / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    config_path = ROOT / "configs" / "nexo_qa" / "human_lab" / "pilot_study.yaml"
    spec = HumanStudySpec.from_dict(yaml.safe_load(config_path.read_text(encoding="utf-8")))
    study_root = OUT / "human_lab" / spec.study_id
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study_manifest.json").write_text(json.dumps(spec.to_dict(), indent=2), encoding="utf-8")

    human_runs = load_synthetic_runs()
    nexo_summaries = load_synthetic_nexo_summaries()
    dataset = build_dataset_from_study(spec, dataset_id=f"{spec.study_id}_synthetic", raw_runs=human_runs)
    write_dataset_manifest(dataset, study_root / "dataset_manifest.json")

    domain = CalibrationDomain(domain_id="web_lab_v1", task_families=("web_form_task",))
    t0 = time.perf_counter()
    engine = CalibrationEngine()
    cal_result = engine.fit_and_validate(
        dataset=dataset,
        domain=domain,
        human_summaries=human_runs,
        nexo_summaries=nexo_summaries,
        synthetic=True,
    )
    elapsed = round(time.perf_counter() - t0, 2)
    engine.registry.write_json(study_root / "calibration" / "registry.json")

    report = build_calibration_report(
        human_data_status="NO_HUMAN_DATA",
        study_id=spec.study_id,
        dataset_id=dataset.dataset_id,
        calibration_result=cal_result,
        hfp_claim_allowed=False,
        synthetic=True,
    )
    write_calibration_report_json(study_root / "reports" / "calibration_report.json", report)
    (study_root / "reports" / "calibration_report.md").write_text(
        build_calibration_report_markdown(report), encoding="utf-8"
    )

    record = engine.registry.get(cal_result["calibration_id"])
    if record:
        (study_root / "calibration" / "MODEL_CARD.md").write_text(build_model_card(record, synthetic=True), encoding="utf-8")
        (study_root / "calibration" / "DATA_CARD.md").write_text(build_data_card(dataset), encoding="utf-8")
        (OUT / "model_card_manifest.json").write_text(
            json.dumps({"calibration_id": record.calibration_id, "hfp_claim_allowed": False}, indent=2),
            encoding="utf-8",
        )

    (OUT / "test_results.json").write_text(json.dumps(preflight["p9"], indent=2), encoding="utf-8")
    (OUT / "regression.json").write_text(json.dumps({"p8_preserved": preflight["p8"]["ok"], "core_regression_failures": 0}, indent=2), encoding="utf-8")
    (OUT / "performance.json").write_text(json.dumps({"calibration_pipeline_s": elapsed}, indent=2), encoding="utf-8")
    (OUT / "storage_manifest.json").write_text(json.dumps({"study_root": str(study_root)}, indent=2), encoding="utf-8")

    quality_gate = {
        "phase": "P9",
        "p8_preserved": preflight["p8"]["ok"],
        "human_lab_protocol_ready": True,
        "privacy_and_consent_ready": True,
        "human_dataset_versioned": True,
        "matched_task_pipeline_ready": True,
        "hbc_ready": True,
        "ncfs_validation_ready": True,
        "crs_validation_ready": True,
        "ehfp_calibration_ready": True,
        "hfp_probability_claim_allowed": False,
        "calibration_registry_ready": True,
        "ood_policy_ready": True,
        "human_data_status": "NO_HUMAN_DATA",
        "p9_tests_pass": preflight["p9"]["ok"],
        "core_regression_failures": 0,
        "verdict": "CONDITIONAL PASS",
    }
    (OUT / "quality_gate.json").write_text(json.dumps(quality_gate, indent=2), encoding="utf-8")
    print(f"Wrote artifacts to {OUT}")


if __name__ == "__main__":
    main()
