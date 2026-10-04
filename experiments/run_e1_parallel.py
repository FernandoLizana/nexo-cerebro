"""Ejecuta condiciones E1 en paralelo (Windows-friendly)."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from brain.experiment_flags import CONDITION_NAMES

from .process_guard import (
    ensure_clean_pipeline,
    ensure_pipeline_hygiene,
    pipeline_env,
    pipeline_root_pid,
)
from .profile_select import profile_label, set_profile_env

ROOT = Path(__file__).resolve().parent.parent


def _run_condition(args: tuple[str, int, int, str, str, int]) -> str:
    condition, seeds, steps, out, profile_key, parallel_seeds = args
    os.environ.setdefault("CEREBRO_OLLAMA", "0")
    os.environ["CEREBRO_EXPERIMENT_PROFILE"] = profile_key
    cmd = [
        sys.executable,
        "-u",
        "-m",
        "experiments.run_batch",
        "--condition",
        condition,
        "--seeds",
        str(seeds),
        "--steps",
        str(steps),
        "--out",
        out,
        "--profile",
        profile_key,
        "--parallel-seeds",
        str(parallel_seeds),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True, env=pipeline_env())
    return condition


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--out", default="experiments/results")
    parser.add_argument("--profile", default="10k", help="compact | 10k")
    parser.add_argument("--workers", type=int, default=0, help="0=auto (2 para 10k)")
    parser.add_argument(
        "--parallel-seeds",
        type=int,
        default=0,
        help="Seeds en paralelo por condición (0=auto: 2 con 10k)",
    )
    parser.add_argument(
        "--conditions",
        default="",
        help="Condiciones E1 separadas por coma (default: todas)",
    )
    parser.add_argument(
        "--turbo-gpu",
        action="store_true",
        help="1 worker + 1 seed/GPU — máximo uso RTX (sin procesos compitiendo)",
    )
    args = parser.parse_args()

    root = pipeline_root_pid()
    if root and root != os.getpid():
        ensure_pipeline_hygiene()
    else:
        ensure_clean_pipeline()
    os.environ.setdefault("CEREBRO_OLLAMA", "0")
    if args.turbo_gpu:
        apply_turbo_gpu_env()
    prof = set_profile_env(args.profile)
    if args.turbo_gpu:
        parallel_seeds = args.parallel_seeds or 1
        workers = args.workers or 1
    else:
        parallel_seeds = args.parallel_seeds or (2 if args.profile.lower().startswith("10") else 1)
        workers = args.workers or (2 if args.profile.lower().startswith("10") else 3)

    conds = [c.strip() for c in args.conditions.split(",") if c.strip()] or list(CONDITION_NAMES)
    invalid = [c for c in conds if c not in CONDITION_NAMES]
    if invalid:
        raise SystemExit(f"Condiciones desconocidas: {invalid} (valid: {CONDITION_NAMES})")

    print(f"E1 paralelo | {profile_label(prof)} | workers={workers} parallel_seeds={parallel_seeds} conds={conds}", flush=True)

    jobs = [
        (c, args.seeds, args.steps, args.out, args.profile.strip().lower(), parallel_seeds)
        for c in conds
    ]
    with ProcessPoolExecutor(max_workers=min(workers, len(jobs))) as pool:
        futures = [pool.submit(_run_condition, j) for j in jobs]
        for fut in as_completed(futures):
            print(f"done: {fut.result()}", flush=True)


def apply_turbo_gpu_env() -> None:
    """Un proceso por GPU — máximo duty cycle CuPy en RTX 6 GB."""
    os.environ["CEREBRO_USE_GPU"] = "1"
    os.environ["CEREBRO_GPU_AGGRESSIVE"] = "1"
    os.environ["CEREBRO_GPU_PERSIST"] = "1"
    os.environ["CEREBRO_GPU_MAX_STEPS"] = "999999"
    os.environ["CEREBRO_GPU_COOLDOWN"] = "0"
    os.environ["CEREBRO_GPU_MIN_STEPS"] = "1"
    os.environ["CEREBRO_MIN_NEURONS_GPU"] = "200"
    os.environ["CEREBRO_HEADLESS_EP_STEPS"] = "64"


if __name__ == "__main__":
    main()
