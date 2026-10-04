"""
Simulaciones en paralelo — varios seeds/procesos (ideal con perfil 10k + GPU).

Cada worker es un proceso independiente con su propio estado y contexto CUDA.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from brain.experiment_flags import CONDITION_NAMES

from .process_guard import ensure_clean_pipeline, pipeline_env
from .profile_select import profile_label, resolve_experiment_profile, set_profile_env

ROOT = Path(__file__).resolve().parent.parent


def _worker_run_seed(job: tuple[str, int, int, str, str]) -> dict:
    condition, seed, steps, out, profile_key = job
    os.environ.setdefault("CEREBRO_OLLAMA", "0")
    os.environ["CEREBRO_EXPERIMENT_PROFILE"] = profile_key
    os.environ.setdefault("CEREBRO_USE_GPU", "1")
    os.environ.setdefault("CEREBRO_GPU_AGGRESSIVE", "1")
    cmd = [
        sys.executable,
        "-u",
        "-m",
        "experiments.run_batch",
        "--condition",
        condition,
        "--seeds",
        "1",
        "--seed-offset",
        str(seed),
        "--steps",
        str(steps),
        "--out",
        out,
        "--profile",
        profile_key,
    ]
    subprocess.run(cmd, cwd=ROOT, check=True, env=pipeline_env())
    return {"condition": condition, "seed": seed}


def _worker_run_condition(job: tuple[str, int, int, str, str]) -> str:
    condition, seeds, steps, out, profile_key = job
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
        str(min(seeds, int(os.environ.get("CEREBRO_PARALLEL_SEEDS", "2")))),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True, env=pipeline_env())
    return condition


def main() -> None:
    parser = argparse.ArgumentParser(description="Nexo — simulaciones paralelas (10k + GPU)")
    parser.add_argument("--profile", default="10k", help="compact | 10k | large")
    parser.add_argument("--condition", default="full", help="full|nobind|...|all")
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--out", default="experiments/results")
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Procesos paralelos (0=auto: 2 con GPU 10k, 4 CPU)",
    )
    parser.add_argument(
        "--mode",
        choices=("seeds", "conditions"),
        default="seeds",
        help="seeds=paralelizar seeds; conditions=paralelizar ablaciones E1",
    )
    args = parser.parse_args()

    ensure_clean_pipeline()
    os.environ.setdefault("CEREBRO_OLLAMA", "0")
    prof = set_profile_env(args.profile)
    workers = args.workers
    if workers <= 0:
        workers = 2 if args.profile.lower().startswith("10") else 4

    print(f"Perfil: {profile_label(prof)}", flush=True)
    print(f"Workers: {workers} | mode={args.mode}", flush=True)

    out = str(Path(args.out))
    pk = args.profile.strip().lower()

    if args.mode == "conditions" or args.condition == "all":
        conds = list(CONDITION_NAMES)
        jobs = [(c, args.seeds, args.steps, out, pk) for c in conds]
        with ProcessPoolExecutor(max_workers=min(workers, len(conds))) as pool:
            for fut in as_completed(pool.submit(_worker_run_condition, j) for j in jobs):
                print(f"done condition: {fut.result()}", flush=True)
        return

    cond = args.condition
    jobs = [(cond, s, args.steps, out, pk) for s in range(args.seeds)]
    with ProcessPoolExecutor(max_workers=min(workers, args.seeds)) as pool:
        for fut in as_completed(pool.submit(_worker_run_seed, j) for j in jobs):
            r = fut.result()
            print(f"done seed {r['seed']} ({r['condition']})", flush=True)


if __name__ == "__main__":
    main()
