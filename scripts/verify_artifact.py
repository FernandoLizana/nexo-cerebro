#!/usr/bin/env python3
"""Verificación robusta del workspace — siempre genera reporte."""

from __future__ import annotations

import importlib
import json
import re
import subprocess
import sys
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_VERSION = "2.1.0"
VERIFICATION_SCOPE = "workspace_verification"

REQUIRED_FILES = (
    "README.md",
    "README_REPRODUCCION.md",
    "pyproject.toml",
    "requirements.txt",
    "LICENSE",
    "CITATION.cff",
    "KNOWN_LIMITATIONS.md",
    "brain/mind.py",
    "nexo/random_streams.py",
    "experiments/run_batch.py",
    "schemas/experiment_result.schema.json",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _reports_dir() -> Path:
    d = _repo_root() / "reports"
    d.mkdir(parents=True, exist_ok=True)
    return d


def safe_import(module_name: str) -> tuple[Any | None, dict[str, str] | None]:
    try:
        return importlib.import_module(module_name), None
    except Exception as exc:
        return None, {"type": type(exc).__name__, "message": str(exc)}


def _parse_junit(path: Path) -> dict[str, int]:
    if not path.is_file():
        return {"tests_collected": 0, "tests_passed": 0, "tests_failed": 0}
    root = ET.parse(path).getroot()
    tests = int(root.attrib.get("tests", 0))
    failures = int(root.attrib.get("failures", 0))
    errors = int(root.attrib.get("errors", 0))
    skipped = int(root.attrib.get("skipped", 0))
    failed = failures + errors
    return {
        "tests_collected": tests,
        "tests_passed": tests - failed - skipped,
        "tests_failed": failed,
        "tests_skipped": skipped,
    }


def _run_pytest(targets: list[str], junit_path: Path) -> dict[str, Any]:
    root = _repo_root()
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *targets,
        "-q",
        "--tb=no",
        f"--junitxml={junit_path}",
    ]
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=900)
    stats = _parse_junit(junit_path)
    stats["exit_code"] = proc.returncode
    # Keep tails relative to repo root so reports stay portable.
    raw_tail = (proc.stdout + proc.stderr).splitlines()[-12:]
    root_s = str(root)
    site = str(Path(sys.executable).resolve().parent)
    scrubbed = []
    for line in raw_tail:
        line = line.replace(root_s, ".").replace(root_s.replace("\\", "/"), ".")
        # Drop absolute interpreter / site-packages paths from warning noise.
        if "site-packages" in line.replace("\\", "/") and ("Users" in line or "home" in line.lower()):
            line = re.sub(
                r"[A-Za-z]:[\\/][^\s\"']+site-packages",
                "<SITE_PACKAGES>",
                line,
            )
        scrubbed.append(line)
    stats["stdout_tail"] = scrubbed
    return stats


def build_report() -> dict[str, Any]:
    root = _repo_root()
    errors: list[str] = []
    warnings: list[str] = []
    report: dict[str, Any] = {
        "status": "fail",
        "verification_scope": VERIFICATION_SCOPE,
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "report_script_version": SCRIPT_VERSION,
        "working_directory": ".",
        "artifact_sha256": None,
        "commit": "NO_GIT_REPOSITORY",
        "dirty_repository": None,
        "python": sys.version.split()[0],
        "tests_collected": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "missing_modules": [],
        "reproducibility_same_seed": False,
        "variability_different_seeds": False,
        "warnings": warnings,
        "errors": errors,
    }

    env_mod, env_err = safe_import("nexo.environment")
    if env_err:
        errors.append(f"import_error:nexo.environment:{env_err['message']}")
    else:
        try:
            report["commit"] = env_mod.git_commit()
            report["dirty_repository"] = env_mod.git_dirty()
        except Exception as exc:  # GitProvenanceError or unexpected
            errors.append(f"git_provenance:{type(exc).__name__}:{exc}")
            warnings.append("git_provenance_unavailable")

    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"missing_required_file:{rel}")

    for mod in ("brain.mind", "brain.deliberation", "nexo.random_streams", "nexo.experiment_conditions"):
        _, err = safe_import(mod)
        if err:
            report["missing_modules"].append(f"{mod}: {err['message']}")
            errors.append(f"module_missing:{mod}")

    junit = _reports_dir() / "pytest-verify-subset.xml"
    pytest_targets = [
        "tests/test_reproducibility.py",
        "tests/test_experiment_conditions.py",
        "tests/test_statistics.py",
        "tests/test_decision_audit.py",
        "tests/test_smoke_results.py",
    ]
    pytest_info = _run_pytest(pytest_targets, junit)
    report["tests_collected"] = pytest_info["tests_collected"]
    report["tests_passed"] = pytest_info["tests_passed"]
    report["tests_failed"] = pytest_info["tests_failed"]
    report["pytest"] = pytest_info
    if pytest_info["exit_code"] != 0:
        errors.append(f"test_failure:exit_code_{pytest_info['exit_code']}")

    rs_mod, rs_err = safe_import("nexo.random_streams")
    if not rs_err:
        a = rs_mod.RandomStreams.from_root_seed(42)
        b = rs_mod.RandomStreams.from_root_seed(42)
        w1 = a.world.random(20)
        w2 = b.world.random(20)
        d1 = a.decision.random(20)
        report["reproducibility_same_seed"] = bool((w1 == w2).all())
        report["variability_different_seeds"] = not bool((w1 == d1).all())

    cond_mod, _ = safe_import("nexo.experiment_conditions")
    if cond_mod:
        unclassified = cond_mod.find_unclassified_enable_flags()
        if unclassified:
            errors.append(f"unclassified_enable_flags:{sorted(unclassified)}")
        full = cond_mod.get_condition("roadmap100_full_v1")
        base = cond_mod.get_condition("baseline_legacy")
        report["config_verification"] = {
            "roadmap100_full_v1_hash": full.config_hash(),
            "baseline_legacy_hash": base.config_hash(),
            "roadmap100_memory_on": full.flags.enable_memory_dynamics,
        }
        nb = cond_mod.get_condition("roadmap100_no_binding_v1")
        if not nb.flags.enable_memory_dynamics:
            errors.append("roadmap100_ablation_not_from_full")

    audit_mod, _ = safe_import("nexo.decision_audit")
    if audit_mod:
        audit = audit_mod.scan_brain_tree()
        report["agency_audit"] = audit
        if audit.get("status") != "audit_pass":
            errors.append(f"agency_audit:{audit.get('status')}")

    smoke_dir = root / "results" / "smoke"
    if smoke_dir.is_dir() and any(smoke_dir.glob("*.json")):
        report["smoke_results_present"] = True
    else:
        warnings.append("smoke_results_missing_run_run_smoke_experiments")

    if errors:
        critical = any(
            k in e
            for e in errors
            for k in ("test_failure", "module_missing", "agency_audit:audit_fail", "missing_required")
        )
        report["status"] = "fail" if critical else "partial"
    else:
        report["status"] = "pass"

    report["errors"] = errors
    report["warnings"] = warnings
    return report


def write_report(report: dict[str, Any]) -> None:
    rd = _reports_dir()
    (rd / "artifact_verification.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    md = [
        "# Verificación workspace NEXO",
        "",
        f"- **Scope:** {report.get('verification_scope')}",
        f"- **Estado:** {report.get('status')}",
        f"- **Generado:** {report.get('report_generated_at')}",
        f"- **Tests:** {report.get('tests_passed')}/{report.get('tests_collected')} passed",
        "",
        "## Errores",
        "",
    ]
    md.extend(f"- {e}" for e in report.get("errors", [])) or md.append("- (ninguno)")
    (rd / "artifact_verification.md").write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    report: dict[str, Any] = {
        "status": "fail",
        "verification_scope": VERIFICATION_SCOPE,
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "report_script_version": SCRIPT_VERSION,
        "errors": ["critical_exception"],
        "warnings": [],
    }
    exit_code = 2
    try:
        report = build_report()
        exit_code = 0 if report["status"] == "pass" else (1 if report["status"] == "fail" else 2)
    except Exception as exc:
        report["errors"] = [f"critical_exception:{type(exc).__name__}:{exc}"]
        report["traceback"] = traceback.format_exc()
    finally:
        write_report(report)
    print(json.dumps({"status": report.get("status"), "errors": len(report.get("errors", []))}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
