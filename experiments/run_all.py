#!/usr/bin/env python3
"""
Pipeline reproducible: E1 ablaciones + E2 LLM + E3 sueño + figuras.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from brain.experiment_flags import CONDITION_NAMES

from .gpu_env import enable_experiment_gpu, gpu_label
from .process_guard import ensure_clean_pipeline, pipeline_env
from .profile_select import profile_label, set_profile_env

ROOT = Path(__file__).resolve().parent.parent


def _run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True, env=pipeline_env())


def main() -> None:
    parser = argparse.ArgumentParser(description="Nexo paper — run all experiments")
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--out", default="experiments/results")
    parser.add_argument("--skip-figures", action="store_true")
    parser.add_argument("--skip-e1", action="store_true", help="Omitir E1 (ya completado)")
    parser.add_argument("--profile", default="10k", help="compact | 10k")
    parser.add_argument("--workers", type=int, default=2, help="Condiciones E1 en paralelo")
    args = parser.parse_args()

    ensure_clean_pipeline()
    os.environ.setdefault("CEREBRO_OLLAMA", "0")
    prof = set_profile_env(args.profile)
    gpu = enable_experiment_gpu()
    if gpu:
        print(f"Compute: {gpu_label()} | {profile_label(prof)}", flush=True)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    py = sys.executable

    if not args.skip_e1:
        _run(
            [
                py,
                "-u",
                "-m",
                "experiments.run_e1_parallel",
                "--seeds",
                str(args.seeds),
                "--steps",
                str(args.steps),
                "--out",
                str(out),
                "--profile",
                args.profile,
                "--workers",
                str(args.workers),
            ]
        )

    _run(
        [
            py,
            "-u",
            "-m",
            "experiments.run_batch",
            "--e2",
            "--seeds",
            str(args.seeds),
            "--steps",
            str(min(args.steps, 100)),
            "--out",
            str(out),
            "--profile",
            args.profile,
            "--parallel-seeds",
            "2",
        ]
    )

    _run(
        [
            py,
            "-u",
            "-m",
            "experiments.run_sleep",
            "--seeds",
            str(args.seeds),
            "--out",
            str(out),
        ]
    )

    if not args.skip_figures:
        _run([py, "-u", "-m", "experiments.plot_figures", "--in", str(out)])

    print(f"\nListo. Resultados en {out.resolve()}")


if __name__ == "__main__":
    main()
