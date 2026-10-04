#!/usr/bin/env python3
"""Orquestador de batería desde YAML."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from nexo.paths import repo_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecutar batería NEXO desde config YAML")
    parser.add_argument("--config", required=True, help="Ruta a battery_*.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Solo imprimir manifiesto")
    args = parser.parse_args()
    path = Path(args.config)
    if not path.is_absolute():
        path = repo_root() / path
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    print(json.dumps(data, indent=2, ensure_ascii=False))
    if args.dry_run:
        return 0
    name = data.get("name", "")
    if name == "battery_ci_compact":
        import subprocess
        import sys

        subprocess.run([sys.executable, "-m", "pytest", "tests/test_reproducibility.py", "-q"], check=False)
        subprocess.run([sys.executable, "-m", "scripts.verify_artifact"], check=False)
        return 0
    print("Batería paper_full requiere ejecución manual experimento por experimento.")
    print("Ver configs/battery_paper_full.yaml y experiments/run_battery_10k.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
