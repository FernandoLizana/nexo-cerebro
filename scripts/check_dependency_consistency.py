#!/usr/bin/env python3
"""Verifica que requirements-lock respete rangos de pyproject.toml."""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Rangos directos del proyecto (fuente principal)
RANGES = {
    "flask": (3, 0, 4, 0),       # >=3.0,<4
    "numpy": (1, 26, 3, 0),      # >=1.26,<3
    "scipy": (1, 11, 2, 0),      # >=1.11,<2
    "pillow": (10, 0, 13, 0),    # >=10,<13 (ajustado)
    "pypdf": (4, 0, 7, 0),       # >=4,<7
    "pyyaml": (6, 0, 7, 0),      # >=6,<7
    "pytest": (8, 0, 9, 0),
    "pytest-cov": (5, 0, 7, 0),
}


def _parse_version(v: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", v)
    return tuple(int(x) for x in parts[:3])


def _in_range(ver: tuple[int, ...], lo: tuple[int, ...], hi: tuple[int, ...]) -> bool:
    def pad(t: tuple[int, ...], n: int) -> tuple[int, ...]:
        return t + (0,) * (n - len(t))

    m = max(len(ver), len(lo), len(hi))
    ver, lo, hi = pad(ver, m), pad(lo, m), pad(hi, m)
    return lo <= ver < hi


def _project_version(root: Path) -> str:
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise SystemExit("pyproject.toml: missing version")
    return match.group(1)


def _citation_version(root: Path) -> str:
    text = (root / "CITATION.cff").read_text(encoding="utf-8")
    match = re.search(r"^version:\s*(\S+)", text, re.MULTILINE)
    if not match:
        raise SystemExit("CITATION.cff: missing version")
    return match.group(1)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    py_ver = _project_version(root)
    cite_ver = _citation_version(root)
    if py_ver != cite_ver:
        print(f"version mismatch: pyproject.toml={py_ver!r} CITATION.cff={cite_ver!r}")
        return 1
    lock = root / "requirements-lock.txt"
    if not lock.is_file():
        print("requirements-lock.txt missing")
        return 1
    errors = []
    for line in lock.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        name, ver = line.split("==", 1)
        key = name.strip().lower().replace("-", "_")
        key_map = {"pyyaml": "pyyaml", "pillow": "pillow", "pytest_cov": "pytest-cov"}
        lookup = key_map.get(key, key.replace("_", "-") if key == "pytest_cov" else key)
        if lookup not in RANGES and key not in RANGES:
            continue
        rk = lookup if lookup in RANGES else key
        lo = RANGES[rk][:2]
        hi = RANGES[rk][2:]
        if not _in_range(_parse_version(ver.strip()), lo, hi):
            errors.append(f"{name}=={ver} outside range for {rk}")
    if errors:
        for e in errors:
            print(e)
        return 1
    print(f"dependency consistency OK (version {py_ver})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
