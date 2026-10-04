"""
Benchmark de latencia/tick y memoria — perfiles LIF (compact / 10k / 50k).

Separa siempre:
  - active_lif = profile_neuron_count (neuronas LIF en RAM)
  - virtual_disk = ensambles indexados (no cuentan como LIF activas)

Uso:
  python -m experiments.bench_tick_gpu --profiles compact,10k
  python -m experiments.bench_tick_gpu --profiles compact,10k,50k   # GPU recomendada
"""

from __future__ import annotations

import argparse
import os
import shutil
import tempfile
import time
from dataclasses import replace
from pathlib import Path

from brain.experiment_flags import AblationFlags
from brain.mind import InfantApeBrain
from brain.profile import profile_neuron_count

from .gpu_env import enable_experiment_gpu, gpu_label, release_experiment_gpu
from .metrics import write_summary_csv
from .process_guard import ensure_clean_pipeline, pipeline_root_pid
from .profile_select import resolve_experiment_profile


def _rss_mb() -> float:
    try:
        import psutil

        return float(psutil.Process(os.getpid()).memory_info().rss) / (1024 * 1024)
    except Exception:
        try:
            import resource

            # Linux: ru_maxrss in KB; Windows Python may lack this
            return float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / 1024.0
        except Exception:
            return -1.0


def _gpu_mem_mb() -> float:
    try:
        from brain.backend import get_backend

        be = get_backend()
        if not be.gpu_available or be._cp is None:
            return -1.0
        cp = be._cp
        free, total = cp.cuda.runtime.memGetInfo()
        used = (total - free) / (1024 * 1024)
        return float(used)
    except Exception:
        return -1.0


def bench_profile(
    profile_key: str,
    *,
    ticks: int = 5,
    warmup: int = 1,
    skip_heavy: bool = True,
) -> dict:
    os.environ.setdefault("CEREBRO_OLLAMA", "0")
    enable_experiment_gpu()
    profile = resolve_experiment_profile(profile_key)
    n_lif = profile_neuron_count(profile)
    row: dict = {
        "profile": profile.name,
        "profile_key": profile_key,
        "active_lif": n_lif,
        "gpu_label": gpu_label(),
        "skipped": False,
        "skip_reason": "",
        "construct_ms": None,
        "ms_per_tick": None,
        "ticks": ticks,
        "rss_mb_peak": None,
        "gpu_mem_mb": None,
        "ok": False,
    }

    # Evitar OOM en CI/CPU: 50k solo si GPU o --force
    if skip_heavy and n_lif >= 40_000:
        from brain.backend import get_backend

        if not get_backend().gpu_available:
            row["skipped"] = True
            row["skip_reason"] = "50k requires GPU (set CEREBRO_USE_GPU=1) or --force-heavy"
            print(
                f"  {profile.name}: SKIP LIF={n_lif} ({row['skip_reason']})",
                flush=True,
            )
            release_experiment_gpu()
            return row

    sd = Path(tempfile.mkdtemp(prefix=f"nexo_bench_{profile_key}_"))
    flags = replace(AblationFlags(), disable_hippocampus=True)
    try:
        rss0 = _rss_mb()
        t0 = time.perf_counter()
        brain = InfantApeBrain(
            profile=profile,
            state_dir=sd,
            headless=True,
            auto_save=False,
            experiment_flags=flags,
        )
        construct_ms = (time.perf_counter() - t0) * 1000.0
        row["construct_ms"] = round(construct_ms, 1)

        for _ in range(max(0, warmup)):
            brain.world_tick(steps=1)

        t1 = time.perf_counter()
        for _ in range(ticks):
            brain.world_tick(steps=1)
        elapsed = time.perf_counter() - t1
        row["ms_per_tick"] = round((elapsed / max(ticks, 1)) * 1000.0, 2)
        row["rss_mb_peak"] = round(max(rss0, _rss_mb()), 1)
        row["gpu_mem_mb"] = round(_gpu_mem_mb(), 1)
        row["ok"] = True
        print(
            f"  {profile.name}: {row['ms_per_tick']} ms/tick | "
            f"LIF={n_lif} | construct={construct_ms:.0f}ms | "
            f"RSS~{row['rss_mb_peak']}MB | {row['gpu_label']}",
            flush=True,
        )
    except Exception as exc:  # noqa: BLE001 — bench must not crash pipeline
        row["skipped"] = True
        row["skip_reason"] = f"{type(exc).__name__}: {exc}"[:160]
        print(f"  {profile.name}: FAIL {row['skip_reason']}", flush=True)
    finally:
        release_experiment_gpu()
        shutil.rmtree(sd, ignore_errors=True)
    return row


def run_bench(
    profiles: list[str],
    *,
    ticks: int,
    out_dir: Path,
    force_heavy: bool,
) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        bench_profile(p, ticks=ticks, skip_heavy=not force_heavy) for p in profiles
    ]
    write_summary_csv(out_dir / "bench_tick_gpu.csv", rows)
    # Resumen HW mínimo legible
    note = out_dir / "bench_hw_notes.md"
    lines = [
        "# Benchmark tick / GPU (auto)",
        "",
        f"- Generado por `experiments.bench_tick_gpu`",
        f"- GPU: `{gpu_label()}`",
        "",
        "| Perfil | LIF activas | ms/tick | RSS MB | Estado |",
        "|--------|------------|---------|--------|--------|",
    ]
    for r in rows:
        if r.get("skipped"):
            lines.append(
                f"| {r['profile']} | {r['active_lif']} | — | — | skip: {r.get('skip_reason','')} |"
            )
        else:
            lines.append(
                f"| {r['profile']} | {r['active_lif']} | {r['ms_per_tick']} | "
                f"{r['rss_mb_peak']} | ok |"
            )
    lines.extend(
        [
            "",
            "## HW mínimo (guía)",
            "",
            "- **compact (~500 LIF):** CPU suficiente; CI / smoke.",
            "- **10k (~10 290 LIF):** GPU NVIDIA + CuPy recomendada para batch paper.",
            "- **50k (≥50 000 LIF):** GPU dedicada (p.ej. RTX 3050 4GB+); no correr en CI sin GPU.",
            "- Nunca citar ensambles en disco como «neuronas activas».",
            "",
        ]
    )
    note.write_text("\n".join(lines), encoding="utf-8")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Nexo tick/GPU benchmark")
    parser.add_argument(
        "--profiles",
        default="compact,10k",
        help="Lista separada por comas: compact,10k,50k",
    )
    parser.add_argument("--ticks", type=int, default=5)
    parser.add_argument("--out", default="experiments/results")
    parser.add_argument(
        "--force-heavy",
        action="store_true",
        help="Forzar 50k aunque no haya GPU (puede OOM)",
    )
    args = parser.parse_args()
    if not pipeline_root_pid():
        ensure_clean_pipeline()
    profiles = [p.strip() for p in args.profiles.split(",") if p.strip()]
    run_bench(
        profiles,
        ticks=args.ticks,
        out_dir=Path(args.out),
        force_heavy=args.force_heavy,
    )


if __name__ == "__main__":
    main()
