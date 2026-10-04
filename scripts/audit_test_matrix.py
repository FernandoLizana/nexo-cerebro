"""Run every tests/ file in its own pytest process with a wall-clock budget.

The aggregate ``pytest tests/`` run can hang, which hides the real pass/fail
picture. Isolating each file keeps one stuck module from masking the rest.
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Per-file budget: pytest's global timeout is 600s; browser suites under load
# can legitimately exceed two minutes, so keep the matrix budget aligned.
TIMEOUT_S = 600
SUMMARY_RE = re.compile(r"(\d+) (passed|failed|error|errors|skipped|xfailed|xpassed)")
FAILED_LINE_RE = re.compile(r"^(?:FAILED|ERROR)\s+(\S+)")


def _parse_junit_failures(junit_path: pathlib.Path) -> list[str]:
    """Return pytest nodeids for failed/errored testcases from a junit XML."""
    if not junit_path.is_file():
        return []
    try:
        root = ET.parse(junit_path).getroot()
    except ET.ParseError:
        return []
    nodeids: list[str] = []
    for case in root.iter("testcase"):
        if case.find("failure") is None and case.find("error") is None:
            continue
        classname = (case.get("classname") or "").strip()
        name = (case.get("name") or "").strip()
        file_attr = (case.get("file") or "").replace("\\", "/")
        if file_attr and name:
            # Prefer path::name so the nodeid matches pytest's usual form.
            rel = file_attr
            if rel.startswith("tests/"):
                nodeids.append(f"{rel}::{name}")
            elif classname:
                # classname is like tests.test_p5_personas
                module = classname.replace(".", "/") + ".py"
                nodeids.append(f"{module}::{name}")
            else:
                nodeids.append(name)
        elif classname and name:
            module = classname.replace(".", "/") + ".py"
            nodeids.append(f"{module}::{name}")
        elif name:
            nodeids.append(name)
    return nodeids


def _parse_stdout_failures(stdout: str) -> list[str]:
    nodeids: list[str] = []
    for line in stdout.splitlines():
        match = FAILED_LINE_RE.match(line.strip())
        if match:
            nodeids.append(match.group(1))
    return nodeids


def run_file(path: pathlib.Path) -> dict:
    started = time.monotonic()
    junit_path = pathlib.Path(tempfile.mkstemp(prefix="matrix_", suffix=".xml")[1])
    try:
        try:
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(path),
                    "-q",
                    "--tb=line",
                    "-p",
                    "no:cacheprovider",
                    f"--junitxml={junit_path}",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=TIMEOUT_S,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            failures = _parse_junit_failures(junit_path) or _parse_stdout_failures(stdout)
            return {
                "file": path.name,
                "status": "timeout",
                "seconds": round(time.monotonic() - started, 1),
                "counts": {},
                "failed_nodeids": failures,
            }
        counts = {kind: int(n) for n, kind in SUMMARY_RE.findall(proc.stdout)}
        if proc.returncode == 0:
            status = "pass"
        elif proc.returncode == 5:
            status = "no_tests"
        else:
            status = "fail"
        failures: list[str] = []
        if status == "fail":
            failures = _parse_junit_failures(junit_path) or _parse_stdout_failures(proc.stdout)
        return {
            "file": path.name,
            "status": status,
            "returncode": proc.returncode,
            "seconds": round(time.monotonic() - started, 1),
            "counts": counts,
            "failed_nodeids": failures,
        }
    finally:
        try:
            junit_path.unlink(missing_ok=True)
        except OSError:
            pass


def main() -> int:
    files = sorted((ROOT / "tests").glob("test_*.py"))
    results = []
    for path in files:
        result = run_file(path)
        results.append(result)
        fail_note = ""
        if result.get("failed_nodeids"):
            fail_note = "  fails=" + ",".join(result["failed_nodeids"])
        print(
            f"{result['status']:<8} {result['seconds']:>6.1f}s  {result['file']}  {result['counts']}{fail_note}",
            flush=True,
        )

    buckets: dict[str, list[str]] = {}
    for result in results:
        buckets.setdefault(result["status"], []).append(result["file"])
    totals: dict[str, int] = {}
    for result in results:
        for kind, n in result["counts"].items():
            totals[kind] = totals.get(kind, 0) + n

    report = {"totals": totals, "by_status": {k: len(v) for k, v in buckets.items()}, "files": results}
    out = ROOT / "reports" / "AUDIT_TEST_MATRIX.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")

    print("\n=== totals ===", flush=True)
    print(json.dumps(report["totals"], ensure_ascii=True), flush=True)
    print(json.dumps(report["by_status"], ensure_ascii=True), flush=True)
    for status in ("fail", "timeout", "no_tests"):
        if buckets.get(status):
            print(f"\n{status}:", flush=True)
            for name in buckets[status]:
                print(f"  {name}", flush=True)
                for result in results:
                    if result["file"] == name and result.get("failed_nodeids"):
                        for nodeid in result["failed_nodeids"]:
                            print(f"    {nodeid}", flush=True)
    print(f"\nwrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
