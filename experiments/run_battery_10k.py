#!/usr/bin/env python3
"""
Batería E1–E8 @10k multi-seed — item 98 (orquestador único).

Modos:
  smoke  — 2 seeds, pocos ticks (minutos; validación pipeline)
  full   — defaults paper (horas en CPU; GPU recomendada para 10k)

Uso:
  python -m experiments.run_battery_10k --mode smoke
  python -m experiments.run_battery_10k --mode full --seeds 20 --out experiments/results/battery_10k
  python -m experiments.run_battery_10k --manifest-only
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from brain.validation_dynamics import BATTERY_E1_E8, ValidationDynamicsStack

from .run_e1_parallel import apply_turbo_gpu_env
from .gpu_env import enable_experiment_gpu, gpu_label
from .process_guard import ensure_clean_pipeline, pipeline_env, pipeline_root_pid
from .profile_select import profile_label, set_profile_env

ROOT = Path(__file__).resolve().parent.parent

SMOKE_DEFAULTS = {"seeds": 2, "steps_e1": 20, "steps_e2": 20}
FULL_DEFAULTS = {"seeds": 20, "steps_e1": 200, "steps_e2": 100}


def _py() -> str:
    return sys.executable


def _run(cmd: list[str], *, label: str) -> float:
    print(f"\n=== {label} ===", flush=True)
    print("+", " ".join(cmd), flush=True)
    t0 = time.perf_counter()
    subprocess.run(cmd, cwd=ROOT, check=True, env=pipeline_env())
    elapsed = time.perf_counter() - t0
    print(f"  done in {elapsed:.1f}s", flush=True)
    return elapsed


def _run_e1(
    *,
    seeds: int,
    steps: int,
    out: Path,
    profile: str,
    parallel_seeds: int,
    smoke: bool,
    turbo: bool = False,
    conditions: str = "",
) -> float:
    ps = 1 if turbo else parallel_seeds
    if smoke:
        return _run(
            [
                _py(),
                "-u",
                "-m",
                "experiments.run_batch",
                "--condition",
                "full",
                "--seeds",
                str(seeds),
                "--steps",
                str(steps),
                "--out",
                str(out),
                "--profile",
                profile,
                "--parallel-seeds",
                str(ps),
            ],
            label="E1 full (smoke)",
        )
    cmd = [
        _py(),
        "-u",
        "-m",
        "experiments.run_e1_parallel",
        "--seeds",
        str(seeds),
        "--steps",
        str(steps),
        "--out",
        str(out),
        "--profile",
        profile,
        "--parallel-seeds",
        str(ps),
        "--workers",
        str(1 if turbo else 2),
    ]
    if turbo:
        cmd.append("--turbo-gpu")
    if conditions:
        cmd.extend(["--conditions", conditions])
    return _run(cmd, label="E1 ablations")


def _run_e2(*, seeds: int, steps: int, out: Path, profile: str, parallel_seeds: int) -> float:
    return _run(
        [
            _py(),
            "-u",
            "-m",
            "experiments.run_batch",
            "--e2",
            "--seeds",
            str(seeds),
            "--steps",
            str(steps),
            "--out",
            str(out),
            "--profile",
            profile,
            "--parallel-seeds",
            str(parallel_seeds),
        ],
        label="E2 LLM invariance",
    )


def _run_e3(*, seeds: int, out: Path) -> float:
    return _run(
        [_py(), "-u", "-m", "experiments.run_sleep", "--seeds", str(seeds), "--out", str(out)],
        label="E3 sleep recall",
    )


def _run_e4(*, seeds: int, out: Path) -> float:
    return _run(
        [_py(), "-u", "-m", "experiments.run_e4_sleep_selective", "--seeds", str(seeds), "--out", str(out)],
        label="E4 selective sleep",
    )


def _run_e5(*, seeds: int, out: Path, profile: str) -> float:
    return _run(
        [
            _py(),
            "-u",
            "-m",
            "experiments.run_e5_grounding",
            "--seeds",
            str(seeds),
            "--out",
            str(out),
            "--profile",
            profile,
        ],
        label="E5 grounding",
    )


def _run_e6(*, out: Path, profile: str) -> float:
    return _run(
        [
            _py(),
            "-u",
            "-m",
            "experiments.bench_tick_gpu",
            "--profiles",
            profile,
            "--ticks",
            "8",
            "--out",
            str(out),
        ],
        label="E6 bench tick",
    )


def _run_e7(*, seeds: int, out: Path, profile: str) -> float:
    return _run(
        [
            _py(),
            "-u",
            "-m",
            "experiments.run_e7_multimodal",
            "--seeds",
            str(seeds),
            "--out",
            str(out),
            "--profile",
            profile,
        ],
        label="E7 multimodal",
    )


def _run_e8(*, seeds: int, out: Path, profile: str) -> float:
    return _run(
        [
            _py(),
            "-u",
            "-m",
            "experiments.run_arena_level24",
            "--seeds",
            str(seeds),
            "--profile",
            profile,
            "--out",
            str(out),
        ],
        label="E8 arena L2.4",
    )


def _run_agency_audit() -> dict:
    from brain.agency_audit import audit_summary

    summary = audit_summary(brain_dir=ROOT / "brain")
    ok = summary["ok"]
    print(f"\n=== Agency audit === ok={ok} violations={len(summary['violations'])}", flush=True)
    if not ok:
        for v in summary["violations"][:8]:
            print(f"  ! {v['path']}:{v['line']} {v['reason']}", flush=True)
    return summary


def run_battery(
    *,
    mode: str = "smoke",
    seeds: int | None = None,
    out: Path | None = None,
    profile: str = "10k",
    parallel_seeds: int = 2,
    only: set[str] | None = None,
    skip_audit: bool = False,
    turbo: bool = False,
    e1_conditions: str = "",
) -> dict:
    smoke = mode == "smoke"
    defaults = SMOKE_DEFAULTS if smoke else FULL_DEFAULTS
    n_seeds = seeds if seeds is not None else defaults["seeds"]
    steps_e1 = defaults["steps_e1"]
    steps_e2 = defaults["steps_e2"]
    compact_seeds = max(1, min(n_seeds, 2 if smoke else n_seeds))

    out_dir = out or Path("experiments/results/_battery_smoke" if smoke else "experiments/results/battery_10k")
    out_dir.mkdir(parents=True, exist_ok=True)

    stack = ValidationDynamicsStack()
    manifest = stack.battery_manifest(profile=profile, seeds=n_seeds if not smoke else 20)

    run_set = {e.experiment_id for e in BATTERY_E1_E8}
    if only:
        run_set &= {x.strip().upper() for x in only}

    if smoke:
        # Smoke @10k: E1+E2; rest compact optional subset
        run_set &= {"E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"}

    timings: dict[str, float] = {}
    started = datetime.now(timezone.utc).isoformat()

    ps = 1 if turbo else parallel_seeds
    if "E1" in run_set:
        timings["E1"] = _run_e1(
            seeds=n_seeds,
            steps=steps_e1,
            out=out_dir,
            profile=profile,
            parallel_seeds=parallel_seeds,
            smoke=smoke,
            turbo=turbo,
            conditions=e1_conditions,
        )
    if "E2" in run_set:
        timings["E2"] = _run_e2(
            seeds=n_seeds,
            steps=steps_e2,
            out=out_dir,
            profile=profile,
            parallel_seeds=ps,
        )
    if "E3" in run_set and not smoke:
        timings["E3"] = _run_e3(seeds=n_seeds, out=out_dir)
    elif "E3" in run_set and smoke:
        timings["E3"] = _run_e3(seeds=min(2, n_seeds), out=out_dir)

    compact_profile = "compact"
    if "E4" in run_set:
        timings["E4"] = _run_e4(seeds=compact_seeds, out=out_dir)
    if "E5" in run_set:
        timings["E5"] = _run_e5(seeds=compact_seeds, out=out_dir, profile=compact_profile)
    if "E6" in run_set:
        timings["E6"] = _run_e6(out=out_dir, profile=profile if not smoke else "compact,10k")
    if "E7" in run_set:
        timings["E7"] = _run_e7(seeds=compact_seeds, out=out_dir, profile=compact_profile)
    if "E8" in run_set:
        timings["E8"] = _run_e8(seeds=compact_seeds, out=out_dir, profile=compact_profile)

    agency = {"skipped": True}
    if not skip_audit:
        agency = _run_agency_audit()

    report = {
        "mode": mode,
        "profile_10k": profile,
        "seeds": n_seeds,
        "steps_e1": steps_e1,
        "steps_e2": steps_e2,
        "experiments_run": sorted(run_set),
        "timings_sec": {k: round(v, 2) for k, v in timings.items()},
        "total_sec": round(sum(timings.values()), 2),
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "gpu": gpu_label(),
        "turbo_gpu": turbo,
        "manifest": manifest,
        "agency_audit": agency,
        "out_dir": str(out_dir.resolve()),
    }
    report_path = out_dir / f"battery_{mode}_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReporte -> {report_path}", flush=True)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Nexo E1–E8 battery @10k")
    parser.add_argument("--mode", choices=("smoke", "full"), default="smoke")
    parser.add_argument("--seeds", type=int, default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--profile", default="10k", help="compact | 10k")
    parser.add_argument("--parallel-seeds", type=int, default=2)
    parser.add_argument("--only", default="", help="Comma list: E1,E2,...")
    parser.add_argument("--skip-audit", action="store_true")
    parser.add_argument("--manifest-only", action="store_true")
    parser.add_argument(
        "--turbo-gpu",
        action="store_true",
        help="1 seed/worker — máximo uso GPU (sin procesos compitiendo)",
    )
    parser.add_argument(
        "--e1-conditions",
        default="",
        help="Solo estas condiciones E1 (coma-separadas)",
    )
    args = parser.parse_args()

    os.environ.setdefault("CEREBRO_OLLAMA", "0")
    if args.turbo_gpu:
        apply_turbo_gpu_env()
    if not pipeline_root_pid():
        ensure_clean_pipeline()

    if args.manifest_only:
        stack = ValidationDynamicsStack()
        manifest = stack.battery_manifest(profile=args.profile, seeds=args.seeds or 20)
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return

    prof = set_profile_env(args.profile)
    gpu = enable_experiment_gpu()
    print(
        f"Battery mode={args.mode} | {profile_label(prof)} | GPU={gpu_label()}",
        flush=True,
    )

    only = {x.strip().upper() for x in args.only.split(",") if x.strip()} or None
    out = Path(args.out) if args.out else None

    report = run_battery(
        mode=args.mode,
        seeds=args.seeds,
        out=out,
        profile=args.profile,
        parallel_seeds=args.parallel_seeds,
        only=only,
        skip_audit=args.skip_audit,
        turbo=args.turbo_gpu,
        e1_conditions=args.e1_conditions,
    )

    if not args.skip_audit:
        audit = report.get("agency_audit") or {}
        if not audit.get("ok", True):
            raise SystemExit(2)

    print(f"\nBatería {args.mode} completada en {report['total_sec']}s -> {report['out_dir']}")


if __name__ == "__main__":
    main()
