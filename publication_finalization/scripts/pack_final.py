#!/usr/bin/env python3
"""
Assemble sanitized zip + PACKAGE_MANIFEST.csv + FINAL_VALIDATION_REPORT.md
+ CLAIM_EVIDENCE_MATRIX + reproducibility sidecars.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PF = ROOT / "publication_finalization"
ZIP_PATH = ROOT / "NEXO_ADAPTIVE_BEHAVIOR_FINAL_PACK.zip"


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git_commit() -> str:
    """Resolve HEAD SHA or fail visibly (never emit NO_GIT_REPOSITORY)."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("cannot resolve git commit: 'git' not on PATH") from exc
    except Exception as exc:
        raise RuntimeError(f"cannot resolve git commit: {exc}") from exc
    commit = (r.stdout or "").strip()
    if r.returncode != 0 or len(commit) != 40:
        detail = (r.stderr or r.stdout or "").strip() or f"exit {r.returncode}"
        raise RuntimeError(f"cannot resolve git commit: {detail}")
    return commit


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_repro_sidecars() -> None:
    (PF / "git_commit.txt").write_text(git_commit() + "\n", encoding="utf-8")
    hw = {
        "timestamp_utc": utc(),
        "os": platform.platform(),
        "python": sys.version,
        "processor": platform.processor(),
        "machine": platform.machine(),
        "cpu_count_logical": os.cpu_count(),
        "git_commit": git_commit(),
        "notes": "RAM ~24GB from host audit; GPU may be absent in this session",
    }
    (PF / "HARDWARE_SOFTWARE.json").write_text(json.dumps(hw, indent=2), encoding="utf-8")

    # pip freeze
    py = sys.executable
    try:
        r = subprocess.run([py, "-m", "pip", "freeze"], capture_output=True, text=True, cwd=ROOT)
        (PF / "requirements-lock.txt").write_text(r.stdout or r.stderr, encoding="utf-8")
    except Exception as e:
        (PF / "requirements-lock.txt").write_text(f"# freeze failed: {e}\n", encoding="utf-8")

    # best-effort environment.yml
    yml = f"""# Best-effort Conda environment sketch — prefer requirements-lock.txt
name: nexo-pub
channels:
  - defaults
dependencies:
  - python=3.11
  - pip
  - pip:
    - -r requirements-lock.txt
"""
    (PF / "environment.yml").write_text(yml, encoding="utf-8")


def sanitize_copy() -> None:
    """Copy only cited modules into relevant_source/."""
    brain_files = [
        "deliberation.py",
        "experiment_flags.py",
        "affordance_map.py",
        "td_reward.py",
        "grounding.py",
        "causal_hud.py",
        "agent_loop.py",
        "body.py",
        "world.py",
        "mind.py",
        "profile.py",
        "neuron.py",
        "sleep_architecture.py",
        "language_cortex.py",
        "intention.py",
    ]
    exp_files = [
        "metrics.py",
        "ablation_flags.py",
        "run_batch.py",
        "plot_figures.py",
        "profile_select.py",
        "README.md",
    ]
    test_files = [
        "test_grounding.py",
        "test_td_reward.py",
        "test_affordance_map.py",
        "test_demo_hud.py",
        "test_s7_scale_motor_multi.py",
        "test_intention_circuit.py",
    ]
    dst_b = PF / "relevant_source" / "brain"
    dst_e = PF / "relevant_source" / "experiments"
    dst_t = PF / "relevant_source" / "tests"
    for d in (dst_b, dst_e, dst_t):
        d.mkdir(parents=True, exist_ok=True)

    copied = []
    skipped = []
    for name in brain_files:
        src = ROOT / "brain" / name
        if src.exists():
            shutil.copy2(src, dst_b / name)
            copied.append(f"brain/{name}")
        else:
            skipped.append(f"brain/{name}")
    for name in exp_files:
        src = ROOT / "experiments" / name
        if src.exists():
            shutil.copy2(src, dst_e / name)
            copied.append(f"experiments/{name}")
        else:
            skipped.append(f"experiments/{name}")
    # arena subset
    arena_dst = dst_e / "arena"
    arena_dst.mkdir(exist_ok=True)
    for name in ("task_transfer_fountain.py", "task_discrimination.py", "__init__.py"):
        src = ROOT / "experiments" / "arena" / name
        if src.exists():
            shutil.copy2(src, arena_dst / name)
            copied.append(f"experiments/arena/{name}")
    for name in test_files:
        src = ROOT / "tests" / name
        if src.exists():
            shutil.copy2(src, dst_t / name)
            copied.append(f"tests/{name}")
        else:
            skipped.append(f"tests/{name}")

    report = [
        "# SANITIZATION_REPORT",
        "",
        f"- timestamp_utc: {utc()}",
        f"- copied_modules: {len(copied)}",
        f"- skipped_missing: {len(skipped)}",
        "",
        "## Included",
        "",
        *[f"- `{c}`" for c in copied],
        "",
        "## Excluded categories (never packed from live tree)",
        "",
        "- `.env`, secrets, credentials",
        "- `.git`, `.venv`, `node_modules`, `__pycache__`",
        "- private DB / large `data/` dumps",
        "- huge JSONL tick dumps from historical E1 (summaries only in historical/)",
        "- Flask demo secrets / Ollama keys",
        "",
        "## Skipped (missing)",
        "",
    ]
    if skipped:
        report.extend(f"- `{s}`" for s in skipped)
    else:
        report.append("- (none)")
    report.append("")
    (PF / "SANITIZATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")


def write_claim_matrix() -> None:
    rows = [
        {
            "claim_id": "C1",
            "claim": "PrefrontalDeliberation is sole choice_key writer under default flags",
            "evidence": "brain/deliberation.py + unit tests + motor audit",
            "status": "VERIFIED",
            "limitation": "Study wrappers intentionally break this for controls",
        },
        {
            "claim_id": "C2",
            "claim": "agency_guard is declarative HUD metadata",
            "evidence": "brain/causal_hud.py; tests/test_demo_hud.py",
            "status": "VERIFIED",
            "limitation": "Not a formal safety proof",
        },
        {
            "claim_id": "C3",
            "claim": "Affordance/TD/grounding are bias-only by default",
            "evidence": "module caps + tests",
            "status": "VERIFIED",
            "limitation": "td_direct study wrapper forces choice",
        },
        {
            "claim_id": "C4",
            "claim": "E1 ablations selectively affect agency/spike_aligned/remembered",
            "evidence": "historical e1_*_summary.csv (10k, n=5)",
            "status": "PARTIALLY VERIFIED",
            "limitation": "Small n; strong determinism; custom metrics",
        },
        {
            "claim_id": "C5",
            "claim": "E2 LLM on/off trajectory invariance (headless)",
            "evidence": "e2_llm_invariance.csv",
            "status": "VERIFIED under protocol",
            "limitation": "Headless may not invoke live LLM",
        },
        {
            "claim_id": "C6",
            "claim": "E3 sleep improves recall score vs control",
            "evidence": "e3_sleep_recall.csv",
            "status": "PARTIALLY VERIFIED",
            "limitation": "Custom metric; small absolute delta",
        },
        {
            "claim_id": "C7",
            "claim": "Compact baselines A comparative table exists",
            "evidence": "raw_results/baselines_A/seed_summaries.csv",
            "status": "NEW_DATA",
            "limitation": "Compact short horizon; not 10k×20",
        },
        {
            "claim_id": "C8",
            "claim": "Agency-break raises override rate vs full",
            "evidence": "raw_results/agency_break_B/",
            "status": "NEW_DATA",
            "limitation": "Control condition; compact",
        },
        {
            "claim_id": "C9",
            "claim": "Env-shift Arena transfer/discrimination multi-seed",
            "evidence": "raw_results/env_shift_C/",
            "status": "NEW_DATA / PARTIAL",
            "limitation": "Compact; ecological validity limited",
        },
        {
            "claim_id": "C10",
            "claim": "Human brain / consciousness / free will / AGI",
            "evidence": "—",
            "status": "NOT CLAIMED",
            "limitation": "Avoid overclaim language",
        },
        {
            "claim_id": "C11",
            "claim": "10k×20 multi-seed replication of E1–E3",
            "evidence": "—",
            "status": "NOT RUN / deferred",
            "limitation": "Compute policy",
        },
        {
            "claim_id": "C12",
            "claim": "External public benchmark comparison",
            "evidence": "—",
            "status": "EVIDENCE MISSING",
            "limitation": "Required for stronger AB Article",
        },
    ]
    path = PF / "CLAIM_EVIDENCE_MATRIX.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_manuscript_facts() -> None:
    text = f"""# MANUSCRIPT_FACTS — Adaptive Behavior (NEXO)

Author: Fernando Andrés Lizana Núñez  
Affiliation: Digital Rider SpA, Chile  
ORCID: **AUTHOR TO CONFIRM**  
Funding: **AUTHOR TO CONFIRM** (none invented)  
Corresponding email: **AUTHOR TO CONFIRM**  
Conflict of interest: **AUTHOR TO CONFIRM**  
Data/code availability statement: **AUTHOR TO CONFIRM** (repo currently private; no push performed)

## Working title (proposal)

Agency-Preserving Action Selection in an Embodied Homeostatic Agent: The NEXO Architecture

## Verified facts safe to cite (with caveats)

- Active LIF counts: compact **624**; 10k profile **10,290** (bench/E1 CSV).
- Historical E1–E3: profile 10k, **n=5 seeds**.
- New baselines A / agency-break B / env-shift C: profile **compact**, **n=20** (primary under `raw_results/n20_compact/`; legacy n=10 preserved), **100 ticks** (A/B).
- Default path: `PrefrontalDeliberation` writes `choice_key`; affordance/TD/grounding bias-only.
- E2: trajectories_identical True for 5/5 under headless protocol.
- Eliasmith 2012 DOI is **10.1126/science.1225266** (correct; drafts had typo).
- Anderson 2004 DOI **10.1037/0033-295X.111.4.1036**.
- `survival_time` formal metric: **MISSING**; study proxies `action_entropy_bits` / `critical_state_tick_*` only.

## Must not claim

- Human brain simulation, consciousness, free will, AGI.
- Demo UI as scientific experiment.
- Invented statistics, DOIs, or unrun 10k×20 replications.

## Placeholders

| Item | Status |
|------|--------|
| Exact submission word count target | AUTHOR TO CONFIRM |
| Preferred Adaptive Behavior article type | AUTHOR TO CONFIRM |
| Ethics / IRB | AUTHOR TO CONFIRM (likely N/A for simulation) |
| Acknowledgments | AUTHOR TO CONFIRM |
| License for code release | AUTHOR TO CONFIRM |

Generated: {utc()}  
git_commit: {git_commit()}
"""
    (PF / "MANUSCRIPT_FACTS.md").write_text(text, encoding="utf-8")


def validation_verdict() -> tuple[str, list[str]]:
    """Return manuscript-facing verdict with honest deferred gaps."""
    issues: list[str] = []
    n20 = PF / "raw_results" / "n20_compact"
    a = n20 / "baselines_A" / "seed_summaries.csv"
    b = n20 / "agency_break_B" / "seed_summaries.csv"
    c = n20 / "env_shift_C" / "env_shift_seed_results.csv"
    # Fall back to legacy n=10 only for presence checks if n20 absent
    a_legacy = PF / "raw_results" / "baselines_A" / "seed_summaries.csv"
    b_legacy = PF / "raw_results" / "agency_break_B" / "seed_summaries.csv"
    c_legacy = PF / "raw_results" / "env_shift_C" / "env_shift_seed_results.csv"
    hist = PF / "raw_results" / "historical" / "e1_full_summary.csv"

    def _n_seeds(path: Path) -> int:
        if not path.exists():
            return 0
        import csv as _csv

        with path.open(encoding="utf-8") as f:
            rows = list(_csv.DictReader(f))
        if not rows:
            return 0
        # count unique seeds for first condition present
        seeds = {r.get("seed") for r in rows if r.get("condition") == rows[0].get("condition")}
        return len(seeds) if seeds else len(rows)

    a_ok = a.exists() or a_legacy.exists()
    b_ok = b.exists() or b_legacy.exists()
    c_ok = c.exists() or c_legacy.exists()
    if not a_ok:
        issues.append("Baselines A seed_summaries missing")
    if not b_ok:
        issues.append("Agency-break B missing")
    if not c_ok:
        issues.append("Env-shift C missing")
    if not hist.exists():
        issues.append("Historical E1 copy missing")

    n20_a = _n_seeds(a) if a.exists() else 0
    n20_complete = a.exists() and b.exists() and c.exists() and n20_a >= 20
    if not n20_complete:
        issues.append("A/B/C compact n=20 campaign incomplete or below n=20")
    issues.append("10k×20 E1–E3 replication NOT RUN (compute policy) — deferred")
    issues.append("External public benchmark EVIDENCE MISSING")
    issues.append("Formal survival_time (death/termination) MISSING; critical_state_tick_* is study proxy only")

    if not a_ok and not hist.exists():
        return "NOT READY — EVIDENCE INSUFFICIENT", issues
    if n20_complete and hist.exists():
        # Manuscript finalization OK with honest deferred list; NOT peer-review ready.
        return "READY FOR MANUSCRIPT FINALIZATION", issues
    return "PARTIALLY READY — MISSING EXPERIMENTS", issues


def write_validation(verdict: str, issues: list[str]) -> None:
    n20 = PF / "raw_results" / "n20_compact"
    a_meta = n20 / "baselines_A" / "run_meta.json"
    b_meta = n20 / "agency_break_B" / "run_meta.json"
    a_seeds = b_seeds = c_seeds = "—"
    a_elapsed = b_elapsed = "—"
    steps = "100"
    if a_meta.exists():
        import json as _json

        m = _json.loads(a_meta.read_text(encoding="utf-8"))
        a_seeds = str(m.get("seeds", "—"))
        steps = str(m.get("steps", 100))
        a_elapsed = str(m.get("elapsed_sec", "—"))
    if b_meta.exists():
        import json as _json

        m = _json.loads(b_meta.read_text(encoding="utf-8"))
        b_seeds = str(m.get("seeds", "—"))
        b_elapsed = str(m.get("elapsed_sec", "—"))
    c_csv = n20 / "env_shift_C" / "env_shift_seed_results.csv"
    if c_csv.exists():
        import csv as _csv

        with c_csv.open(encoding="utf-8") as f:
            rows = list(_csv.DictReader(f))
        c_seeds = str(len({r.get("seed") for r in rows})) if rows else "—"

    e10k = n20 / "e10k_smoke" / "seed_summaries.csv"
    e10k_note = "optional; see SMOKE_NOTE" if e10k.exists() else "deferred / not run this session"

    lines = [
        "# FINAL_VALIDATION_REPORT",
        "",
        f"- timestamp_utc: {utc()}",
        f"- git_commit: `{git_commit()}`",
        "",
        "## Conclusion",
        "",
        verdict,
        "",
        "## What was run",
        "",
        "| Block | Profile | Seeds | Notes |",
        "|-------|---------|-------|-------|",
        f"| A Baselines | compact | {a_seeds} | {steps} ticks; study wrappers; under `raw_results/n20_compact/`; elapsed≈{a_elapsed}s |",
        f"| B Agency-break | compact | {b_seeds} | control vs full; elapsed≈{b_elapsed}s |",
        f"| C Env shift | compact | {c_seeds} | transfer + discrimination Arena |",
        "| D Historical E1-E3 | 10k | 5 | copied; not re-run |",
        "| D Smoke | compact | 2 | short ticks (prior) |",
        f"| E Optional 10k smoke | 10k | 2×2 | {e10k_note} |",
        "| E Motor audit | n/a | n/a | static + pytest |",
        "",
        "## Deferred (explicit)",
        "",
        "- Full plan 6×20×long @10k baselines",
        "- E1–E3 multi-seed **10k × 20** replication (NOT RUN — do not claim peer-review ready on this alone)",
        "- Formal survival_time until death/termination; public ecological benchmark",
        "",
        "## Issues / gaps",
        "",
        *[f"- {i}" for i in issues],
        "",
        "## Honesty",
        "",
        "- Do **not** claim READY FOR PEER REVIEW while 10k×20 is missing.",
        "- Compact n=20 A/B/C is the primary comparison for manuscript drafting; historical 10k n=5 remains separate.",
        "- Legacy n=10 under `raw_results/baselines_A/` etc. preserved; primary pack uses n20_compact.",
        "",
        "## Zip",
        "",
        f"- `{ZIP_PATH.name}` at repo root (mirrored under publication_finalization/)",
        "",
    ]
    (PF / "FINAL_VALIDATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def build_zip() -> list[tuple[str, str, int]]:
    """Return manifest rows (relpath, sha256, size)."""
    exclude_dir_names = {
        ".git",
        ".venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        "data",
    }
    exclude_file_suffixes = (".env", ".jsonl")  # skip huge tick dumps in pack
    # Allow small jsonl? Policy says huge jsonl — we didn't write jsonl by default.

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    manifest: list[tuple[str, str, int]] = []
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(PF.rglob("*")):
            if not path.is_file():
                continue
            if any(p in exclude_dir_names for p in path.parts):
                continue
            if path.suffix.lower() == ".jsonl":
                continue  # exclude tick dumps from zip
            if path.suffix.lower() == ".zip":
                continue  # avoid nesting the package zip
            if path.name.startswith(".env"):
                continue
            rel = path.relative_to(ROOT).as_posix()
            zf.write(path, arcname=rel)
            digest = sha256_file(path)
            manifest.append((rel, digest, path.stat().st_size))

        # also include top-level zip pointer note inside? skip
    # Mirror zip into publication_finalization
    shutil.copy2(ZIP_PATH, PF / ZIP_PATH.name)
    return manifest


def write_manifest(rows: list[tuple[str, str, int]]) -> None:
    path = PF / "PACKAGE_MANIFEST.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["relpath", "sha256", "size_bytes"])
        for rel, digest, size in rows:
            w.writerow([rel, digest, size])
        # append zip itself hash
        if ZIP_PATH.exists():
            w.writerow([ZIP_PATH.name, sha256_file(ZIP_PATH), ZIP_PATH.stat().st_size])


def main() -> None:
    write_repro_sidecars()
    sanitize_copy()
    write_claim_matrix()
    write_manuscript_facts()
    verdict, issues = validation_verdict()
    write_validation(verdict, issues)
    rows = build_zip()
    write_manifest(rows)
    # refresh validation with zip size
    print("Verdict:", verdict)
    print("Zip:", ZIP_PATH, "bytes=", ZIP_PATH.stat().st_size if ZIP_PATH.exists() else 0)
    print("Manifest entries:", len(rows))


if __name__ == "__main__":
    main()
