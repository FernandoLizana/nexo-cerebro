"""Bench GPU/LIF seguro para CI (Sprint 37)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def run_gpu_bench_ci(*, profile_key: str = "compact", ticks: int = 1) -> dict[str, Any]:
    """Ejecuta bench legacy mínimo; omite en CI si NEXO_SKIP_GPU_BENCH=1."""
    if os.environ.get("NEXO_SKIP_GPU_BENCH", "").strip() in ("1", "true", "yes"):
        return {
            "skipped": True,
            "reason": "NEXO_SKIP_GPU_BENCH",
            "profile_key": profile_key,
        }
    from nexo.behavioral.lif_scale import probe_lif_scale_availability, run_lif_scale_probe

    probe = probe_lif_scale_availability()
    if not probe.get("available"):
        return {"skipped": True, "reason": "gpu_unavailable", **probe}
    bench = run_lif_scale_probe(profile_key=profile_key, ticks=ticks)
    return {
        "skipped": False,
        "profile_key": profile_key,
        "ticks": ticks,
        "ci_safe": True,
        "probe": probe,
        "bench": bench,
    }


def export_gpu_bench(
    output_path: Path,
    *,
    profile_key: str = "compact",
    ticks: int = 1,
    ci_safe: bool = True,
) -> dict[str, Any]:
    payload = run_gpu_bench_ci(profile_key=profile_key, ticks=ticks) if ci_safe else {}
    if not payload:
        payload = {"skipped": True, "reason": "empty"}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "exported": True,
        "path": str(output_path),
        "skipped": payload.get("skipped", False),
        "gpu_label": (payload.get("probe") or {}).get("gpu_label"),
    }
