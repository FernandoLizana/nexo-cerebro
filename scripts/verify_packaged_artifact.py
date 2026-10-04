#!/usr/bin/env python3
"""Verifica el ZIP extraído en carpeta limpia."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_VERSION = "1.0.0"


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _rel_or_name(path: Path) -> str:
    """Emit path relative to repo root when possible; never absolute home paths."""
    root = _repo_root()
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reports_dir() -> Path:
    d = _repo_root() / "reports"
    d.mkdir(parents=True, exist_ok=True)
    return d


def build_or_use_artifact(artifact: Path | None) -> Path:
    if artifact and artifact.is_file():
        return artifact
    from scripts.build_release_artifact import build

    return build()


def verify_packaged(
    artifact: Path,
    *,
    keep_temp: bool = False,
    skip_install: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "status": "fail",
        "verification_scope": "packaged_artifact_verification",
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_path": _rel_or_name(artifact),
        "artifact_sha256": _sha256(artifact),
        "temporary_directory": None,
        "installation_success": False,
        "tests_collected": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "smoke_runs_completed": 0,
        "verify_artifact_status": "not_run",
        "missing_required_paths": [],
        "personal_paths_detected": [],
        "errors": [],
        "warnings": [],
    }

    if artifact.stat().st_size == 0:
        report["errors"].append("artifact_empty")
        return report

    tmp = Path(tempfile.mkdtemp(prefix="nexo_pkg_verify_"))
    report["temporary_directory"] = f"<TEMP>/{tmp.name}"
    try:
        with zipfile.ZipFile(artifact, "r") as zf:
            names = zf.namelist()
            if not names:
                report["errors"].append("zip_no_entries")
                return report
            for req in ("brain/", "nexo/", "experiments/", "tests/", "pyproject.toml"):
                if not any(n == req.rstrip("/") or n.startswith(req) for n in names):
                    report["missing_required_paths"].append(req)
            # Detect absolute home/lab paths without hardcoding a username.
            personal_re = re.compile(
                r"(?i)(?:Users|home)[/\\][^/\\\s\"']+|OneDrive|Escritorio[/\\]cerebro"
            )
            skip_personal_scan = {
                "scripts/build_release_artifact.py",
                "scripts/generate_repository_inventory.py",
                "scripts/verify_packaged_artifact.py",
            }
            for n in names:
                if "__pycache__" in n or n.endswith(".pyc"):
                    report["errors"].append(f"cache_in_zip:{n}")
                if n in skip_personal_scan or n.startswith("reports/") or n.startswith("docs/"):
                    continue
                try:
                    if n.endswith((".py", ".md", ".json")):
                        data = zf.read(n)[:4000].decode("utf-8", errors="replace")
                        if personal_re.search(data):
                            report["personal_paths_detected"].append(n)
                except Exception:
                    pass
            if report["missing_required_paths"]:
                report["errors"].append("missing_required_in_zip")
            if report["personal_paths_detected"]:
                report["errors"].append("personal_paths_in_zip")
            zf.extractall(tmp)

        run_env = os.environ.copy()
        run_env["PYTHONPATH"] = str(tmp) + os.pathsep + run_env.get("PYTHONPATH", "")

        if not skip_install:
            pip_cmd = [sys.executable, "-m", "pip", "install", "-e", f".[dev]"]
            proc = subprocess.run(pip_cmd, cwd=tmp, capture_output=True, text=True, timeout=600)
            report["installation_success"] = proc.returncode == 0
            if proc.returncode != 0:
                report["errors"].append(f"pip_install_failed:{proc.returncode}")
                if verbose:
                    report["pip_stderr"] = proc.stderr[-2000:]

        smoke = subprocess.run(
            [sys.executable, "-m", "experiments.run_smoke_experiments"],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=600,
            env=run_env,
        )
        if smoke.returncode == 0:
            report["smoke_runs_completed"] = 5
        else:
            report["errors"].append(f"smoke_failed:{smoke.returncode}")
            if verbose:
                report["smoke_stderr"] = (smoke.stderr or smoke.stdout)[-3000:]

        verify = subprocess.run(
            [sys.executable, "-m", "scripts.verify_artifact"],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=900,
            env=run_env,
        )
        verify_json = tmp / "reports" / "artifact_verification.json"
        if verify_json.is_file():
            vdata = json.loads(verify_json.read_text(encoding="utf-8"))
            report["verify_artifact_status"] = vdata.get("status", "unknown")
            report["tests_collected"] = vdata.get("tests_collected", 0)
            report["tests_passed"] = vdata.get("tests_passed", 0)
            report["tests_failed"] = vdata.get("tests_failed", 0)
        else:
            report["errors"].append("verify_report_missing_in_extract")
        if verify.returncode != 0:
            report["errors"].append(f"verify_exit_{verify.returncode}")

        critical = any(
            e.startswith(x)
            for e in report["errors"]
            for x in ("missing_required", "personal_paths", "artifact_empty", "pip_install", "verify_exit")
        )
        if not report["errors"]:
            report["status"] = "pass"
        elif critical:
            report["status"] = "fail"
        else:
            report["status"] = "partial"
    finally:
        if not keep_temp:
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            report["warnings"].append("temp_dir_kept")

    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, default=None)
    parser.add_argument("--keep-temp", action="store_true")
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    artifact = build_or_use_artifact(args.artifact)
    report = verify_packaged(
        artifact,
        keep_temp=args.keep_temp,
        skip_install=args.skip_install,
        verbose=args.verbose,
    )
    rd = _reports_dir()
    (rd / "packaged_artifact_verification.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    md = [
        "# Verificación paquete extraído",
        "",
        f"- **Estado:** {report['status']}",
        f"- **SHA256:** {report['artifact_sha256']}",
        f"- **Instalación:** {report['installation_success']}",
        f"- **Smoke runs:** {report['smoke_runs_completed']}",
        f"- **verify_artifact:** {report['verify_artifact_status']}",
    ]
    (rd / "PACKAGED_ARTIFACT_VERIFICATION.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"status": report["status"], "errors": len(report["errors"])}, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
