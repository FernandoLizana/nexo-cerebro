"""
Runner headless para ablaciones (E1) y comparación LLM (E2).
Soporta perfil 10k y seeds en paralelo.
"""

from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from brain.experiment_flags import apply_condition
from brain.mind import InfantApeBrain
from brain.profile import NeuroProfile, profile_neuron_count

from brain.backend import get_backend, reset_backend

from .gpu_env import enable_experiment_gpu, release_experiment_gpu
from .process_guard import ensure_clean_pipeline, pipeline_root_pid
from .profile_select import resolve_experiment_profile

from .metrics import MetricsLogger, TickMetrics, extract_tick_metrics, write_summary_csv


def _profile() -> NeuroProfile:
    return resolve_experiment_profile()


def make_brain(
    seed: int,
    condition: str,
    *,
    state_root: Path | None = None,
    profile: NeuroProfile | None = None,
) -> InfantApeBrain:
    np.random.seed(seed)
    sd = state_root
    if sd is None:
        sd = Path(tempfile.mkdtemp(prefix=f"nexo_{condition}_{seed}_"))
    p = profile or _profile()
    brain = InfantApeBrain(
        profile=p,
        state_dir=sd,
        headless=True,
        auto_save=False,
        experiment_flags=apply_condition(condition),
    )
    brain.world._rng = np.random.default_rng(seed)  # noqa: SLF001
    return brain


def run_simulation(
    *,
    condition: str = "full",
    seed: int = 0,
    steps: int = 200,
    state_root: Path | None = None,
    jsonl_path: Path | None = None,
    profile: NeuroProfile | None = None,
) -> tuple[list[TickMetrics], dict]:
    os.environ.setdefault("CEREBRO_OLLAMA", "0")
    gpu = enable_experiment_gpu()
    p = profile or _profile()
    brain = make_brain(seed, condition, state_root=state_root, profile=p)
    logger = MetricsLogger(jsonl_path or Path("experiments/results/_scratch.jsonl"))
    if jsonl_path and jsonl_path.exists():
        jsonl_path.unlink()

    try:
        for t in range(steps):
            out = brain.world_tick(steps=1)
            row = extract_tick_metrics(out, tick=t, seed=seed, condition=condition)
            logger.log(row)
    finally:
        release_experiment_gpu()

    be = get_backend()
    summary = logger.summary()
    summary.update(
        {
            "seed": seed,
            "condition": condition,
            "steps": steps,
            "compute": be.label,
            "gpu_steps_last_episode": be._gpu_steps_this_episode,
            "profile": p.name,
            "n_neurons": profile_neuron_count(p),
        }
    )
    return logger.rows, summary


def _run_one_seed_job(
    condition: str,
    seed: int,
    steps: int,
    out: Path,
) -> dict:
    """Job picklable para ProcessPoolExecutor (Windows spawn)."""
    os.environ.setdefault("CEREBRO_OLLAMA", "0")
    sd = Path(tempfile.mkdtemp(prefix=f"nexo_{condition}_{seed}_"))
    jsonl = out / f"e1_{condition}_s{seed}.jsonl"
    try:
        _, summary = run_simulation(
            condition=condition,
            seed=seed,
            steps=steps,
            state_root=sd,
            jsonl_path=jsonl,
        )
        return summary
    finally:
        shutil.rmtree(sd, ignore_errors=True)


def run_llm_invariance(
    seed: int = 0,
    steps: int = 100,
    out_dir: Path | None = None,
) -> dict:
    """E2: mismas trayectorias motoras/deliberación con LLM on vs off."""
    out_dir = out_dir or Path("experiments/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    traces: dict[str, list[dict]] = {}

    for label, ollama in (("llm_off", "0"), ("llm_on", "1")):
        os.environ["CEREBRO_OLLAMA"] = ollama
        os.environ["CEREBRO_USE_GPU"] = "0"
        reset_backend()
        sd = Path(tempfile.mkdtemp(prefix=f"nexo_e2_{label}_"))
        jsonl = out_dir / f"e2_{label}_s{seed}.jsonl"
        if jsonl.exists():
            jsonl.unlink()
        try:
            rows, _ = run_simulation(
                condition="full",
                seed=seed,
                steps=steps,
                state_root=sd,
                jsonl_path=jsonl,
            )
            traces[label] = [
                {
                    "tick": r.tick,
                    "choice_key": r.choice_key,
                    "inhibited": r.inhibited,
                    "pfc_veto": r.pfc_veto,
                    "agent_x": r.agent_x,
                    "agent_y": r.agent_y,
                    "motor": r.motor,
                    "agency": r.agency,
                }
                for r in rows
            ]
        finally:
            shutil.rmtree(sd, ignore_errors=True)

    off = traces["llm_off"]
    on = traces["llm_on"]

    def _match(o: dict, n: dict) -> bool:
        return (
            o["choice_key"] == n["choice_key"]
            and bool(o["inhibited"]) == bool(n["inhibited"])
            and bool(o["pfc_veto"]) == bool(n["pfc_veto"])
            and o["motor"] == n["motor"]
        )

    identical = len(off) == len(on) and all(_match(o, n) for o, n in zip(off, on))
    return {
        "seed": seed,
        "steps": steps,
        "trajectories_identical": identical,
        "n_ticks": len(off),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Nexo batch experiments (headless)")
    parser.add_argument("--condition", default="full", help="full|nobind|nopfc|nohippo|noaffect")
    parser.add_argument("--seeds", type=int, default=5, help="Número de seeds")
    parser.add_argument("--seed-offset", type=int, default=0, help="Primer seed (para workers)")
    parser.add_argument("--steps", type=int, default=200, help="Ticks por run")
    parser.add_argument("--out", default="experiments/results", help="Directorio de salida")
    parser.add_argument("--profile", default=None, help="compact | 10k | large")
    parser.add_argument(
        "--parallel-seeds",
        type=int,
        default=1,
        help="Seeds simultáneos (2 recomendado RTX 6GB con 10k)",
    )
    parser.add_argument("--e2", action="store_true", help="Correr E2 LLM invariance")
    args = parser.parse_args()

    root = pipeline_root_pid()
    if not root:
        ensure_clean_pipeline()

    if args.profile:
        os.environ["CEREBRO_EXPERIMENT_PROFILE"] = args.profile
    os.environ.setdefault("CEREBRO_OLLAMA", "0")
    prof = resolve_experiment_profile()
    print(
        f"Perfil {prof.name} (~{profile_neuron_count(prof)} neuronas) | "
        f"parallel_seeds={args.parallel_seeds}",
        flush=True,
    )

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    if args.e2:
        e2_rows: list[dict] = []
        for s in range(args.seed_offset, args.seed_offset + args.seeds):
            e2_rows.append(run_llm_invariance(seed=s, steps=args.steps, out_dir=out))
            print(f"  E2 seed={s} identical={e2_rows[-1]['trajectories_identical']}", flush=True)
        write_summary_csv(out / "e2_llm_invariance.csv", e2_rows)
        print(f"E2 completado -> {out / 'e2_llm_invariance.csv'}")
        return

    seed_list = list(range(args.seed_offset, args.seed_offset + args.seeds))
    summaries: list[dict] = []

    if args.parallel_seeds > 1 and len(seed_list) > 1:
        workers = min(args.parallel_seeds, len(seed_list))
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futs = {
                pool.submit(_run_one_seed_job, args.condition, s, args.steps, out): s
                for s in seed_list
            }
            for fut in as_completed(futs):
                s = futs[fut]
                summary = fut.result()
                summaries.append(summary)
                print(
                    f"  {args.condition} seed={s} agency={summary.get('mean_agency', 0):.3f}",
                    flush=True,
                )
    else:
        for seed in seed_list:
            sd = Path(tempfile.mkdtemp(prefix=f"nexo_{args.condition}_{seed}_"))
            jsonl = out / f"e1_{args.condition}_s{seed}.jsonl"
            try:
                _, summary = run_simulation(
                    condition=args.condition,
                    seed=seed,
                    steps=args.steps,
                    state_root=sd,
                    jsonl_path=jsonl,
                )
                summaries.append(summary)
                print(
                    f"  {args.condition} seed={seed} agency={summary.get('mean_agency', 0):.3f}",
                    flush=True,
                )
            finally:
                shutil.rmtree(sd, ignore_errors=True)

    summaries.sort(key=lambda r: int(r.get("seed", 0)))
    csv_name = f"e1_{args.condition}_summary.csv"
    write_summary_csv(out / csv_name, summaries)
    print(f"E1 {args.condition} -> {out / csv_name} ({len(summaries)} seeds)")


if __name__ == "__main__":
    main()
