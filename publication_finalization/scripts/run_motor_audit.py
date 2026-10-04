#!/usr/bin/env python3
"""Motor audit: static grep + targeted pytest → publication_finalization report."""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "publication_finalization" / "raw_results" / "motor_audit_E"
OUT.mkdir(parents=True, exist_ok=True)

ASSIGN_RE = re.compile(r"choice_key\s*=")


def scan() -> list[str]:
    lines: list[str] = []
    for path in (ROOT / "brain").rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            if ASSIGN_RE.search(line) and not line.strip().startswith("#"):
                lines.append(f"{path.relative_to(ROOT)}:{i}:{line.strip()}")
    return lines


def main() -> None:
    hits = scan()
    (OUT / "choice_key_assignments.txt").write_text("\n".join(hits) + "\n", encoding="utf-8")
    writer_hits = [h for h in hits if "deliberation.py" in h and "winner.key" in h]
    report = [
        f"timestamp_utc={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"assignment_sites={len(hits)}",
        f"deliberation_winner_key_sites={len(writer_hits)}",
        "primary_writer_claim=PrefrontalDeliberation.run assigns choice_key=winner.key",
        "other_sites=plumbing/tests/memory — see choice_key_assignments.txt",
    ]
    (OUT / "static_scan_summary.txt").write_text("\n".join(report) + "\n", encoding="utf-8")

    tests = [
        "tests/test_grounding.py",
        "tests/test_td_reward.py",
        "tests/test_affordance_map.py",
        "tests/test_demo_hud.py",
        "tests/test_s7_scale_motor_multi.py",
    ]
    cmd = [sys.executable, "-m", "pytest", *tests, "-q", "--tb=line"]
    env = dict(**{k: v for k, v in __import__("os").environ.items()})
    env["CEREBRO_SKIP_PROCESS_GUARD"] = "1"
    env["CEREBRO_OLLAMA"] = "0"
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)
    (OUT / "pytest_agency.txt").write_text(
        f"cmd={' '.join(cmd)}\nexit={proc.returncode}\n\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}\n",
        encoding="utf-8",
    )
    print(proc.stdout)
    print("motor audit exit", proc.returncode)
    raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
