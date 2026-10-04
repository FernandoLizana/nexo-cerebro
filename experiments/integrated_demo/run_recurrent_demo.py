#!/usr/bin/env python3
"""Demo recurrente mínima — percepción → atención → memoria → decisión → acción."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig


def main() -> int:
    root = Path(__file__).resolve().parent.parent.parent
    profiles = (
        ("integrated_v1", IntegratedRuntimeConfig(seed=42, ticks=80, profile="integrated_v1")),
        ("integrated_no_attention", IntegratedRuntimeConfig(
            seed=42, ticks=80, profile="integrated_no_attention",
            disable_processes=("attention",),
        )),
    )
    results = {}
    for name, cfg in profiles:
        rt = IntegratedRuntime(config=cfg)
        results[name] = rt.run()

    out_dir = root / "results" / "integrated_demo"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "recurrent_demo.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"written": str(out_path), "profiles": list(results.keys())}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
