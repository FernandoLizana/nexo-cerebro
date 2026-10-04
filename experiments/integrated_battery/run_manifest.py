"""Ejecutor de batería desde manifiesto YAML reproducible."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from nexo.behavioral.manifest import execute_manifest


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="experiments.integrated_battery.run_manifest")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("configs/battery/integrated_v2.yaml"),
    )
    args = parser.parse_args(argv)
    summary = execute_manifest(args.manifest)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
