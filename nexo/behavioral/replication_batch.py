"""Réplicas multi-seed automatizadas (Sprint 19)."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any


def run_replication_batch_from_config(
    cfg_template: Any,
    seeds: tuple[int, ...],
    base_dir: Path,
    *,
    ticks: int | None = None,
) -> dict[str, Any]:
    """Ejecuta y exporta un paquete de replicación por seed."""
    from nexo.integrated_runtime import IntegratedRuntime

    base_dir.mkdir(parents=True, exist_ok=True)
    bundles: list[dict[str, Any]] = []
    for seed in seeds:
        cfg = replace(cfg_template, seed=seed)
        if ticks is not None:
            cfg = replace(cfg, ticks=ticks)
        rt = IntegratedRuntime(cfg)
        result = rt.run()
        out_dir = base_dir / f"seed_{seed}"
        meta = rt.export_replication(out_dir, result)
        bundles.append({"seed": seed, **meta})
    summary = {
        "n_seeds": len(seeds),
        "seeds": list(seeds),
        "output_root": str(base_dir),
        "bundles": bundles,
    }
    (base_dir / "batch_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return summary


def run_replication_batch(
    config_path: Path,
    seeds: tuple[int, ...],
    base_dir: Path,
    *,
    ticks: int | None = None,
) -> dict[str, Any]:
    from nexo.integrated_runtime import runtime_from_config

    rt = runtime_from_config(config_path)
    return run_replication_batch_from_config(rt.config, seeds, base_dir, ticks=ticks)
