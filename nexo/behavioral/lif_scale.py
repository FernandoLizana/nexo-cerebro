"""Sonda escala LIF/GPU legacy (Sprint 33)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def probe_lif_scale_availability() -> dict[str, Any]:
    try:
        from experiments.gpu_env import gpu_label

        gpu = gpu_label()
    except Exception as exc:
        return {"available": False, "error": str(exc)}
    return {
        "available": True,
        "gpu_label": gpu,
        "bench_module": "experiments.bench_tick_gpu",
        "default_profile": "compact",
    }


def run_lif_scale_probe(
    *,
    profile_key: str = "compact",
    ticks: int = 2,
) -> dict[str, Any]:
    """Ejecuta bench legacy compact (puede tardar; no es runtime integrado)."""
    probe = probe_lif_scale_availability()
    if not probe.get("available"):
        return probe
    try:
        from experiments.bench_tick_gpu import bench_profile

        row = bench_profile(profile_key, ticks=ticks, skip_heavy=True)
        return {
            "available": True,
            "profile_key": profile_key,
            "bench": row,
        }
    except Exception as exc:
        return {"available": False, "error": str(exc), "profile_key": profile_key}


def export_lif_scale_probe(
    output_path: Path,
    *,
    profile_key: str = "compact",
    ticks: int = 2,
    run_bench: bool = False,
) -> dict[str, Any]:
    payload = probe_lif_scale_availability()
    if run_bench:
        payload["probe"] = run_lif_scale_probe(profile_key=profile_key, ticks=ticks)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), "gpu_label": payload.get("gpu_label")}
