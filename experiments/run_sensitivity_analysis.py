#!/usr/bin/env python3
"""Análisis de sensibilidad compacto (no ejecutar grid completo en CI)."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import yaml

from nexo.paths import repo_root, reports_dir


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/sensitivity_compact.yaml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    cfg_path = repo_root() / args.config
    if not cfg_path.exists():
        sample = {
            "parameters": {
                "deliberation.noise_scale": [0.02, 0.055, 0.08],
            },
            "seeds": [0, 1],
            "steps": 10,
            "note": "Ejecutar manualmente; perfil compacto",
        }
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(yaml.dump(sample), encoding="utf-8")
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    out = reports_dir() / "sensitivity_analysis.json"
    out.write_text(json.dumps({"config": data, "status": "defined_not_run"}, indent=2), encoding="utf-8")
    csv_path = reports_dir() / "sensitivity_analysis.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["parameter", "value", "status"])
        for param, values in (data.get("parameters") or {}).items():
            for v in values:
                w.writerow([param, v, "pending"])
    if args.dry_run:
        print(json.dumps(data, indent=2))
    else:
        print(f"Plantilla escrita: {out}; ejecutar grid manualmente")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
