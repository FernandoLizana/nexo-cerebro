#!/usr/bin/env python3
"""Genera reports/repository_inventory.json desde el repo real."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PERSONAL_MARKERS = (
    "OneDrive",
    "Escritorio/cerebro",
    "Escritorio\\cerebro",
)
PERSONAL_PATH_REGEX = re.compile(
    r"(?i)(?:^|[^\w])(?:Users|home)[/\\][^/\\\s\"']+",
)

KEY_DIRS = (
    "brain",
    "nexo",
    "experiments",
    "scripts",
    "tests",
    "configs",
    "schemas",
    "reports",
    "docs",
    "roadmap",
    ".github",
)

EXCLUDE_PARTS = {".venv", "venv", "__pycache__", ".git", "node_modules"}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _scan_dir(root: Path, name: str) -> dict:
    p = root / name
    if not p.exists():
        return {"exists": False, "path": name}
    files = [f for f in p.rglob("*") if f.is_file() and not any(x in f.parts for x in EXCLUDE_PARTS)]
    py_files = [f for f in files if f.suffix == ".py"]
    personal = []
    for f in files:
        if f.suffix in {".py", ".md", ".json", ".yaml", ".txt", ".cff"}:
            try:
                text = f.read_text(encoding="utf-8", errors="replace")[:4000]
            except OSError:
                continue
            if any(m in text for m in PERSONAL_MARKERS) or PERSONAL_PATH_REGEX.search(text):
                personal.append(str(f.relative_to(root).as_posix()))
    return {
        "exists": True,
        "path": name,
        "file_count": len(files),
        "python_file_count": len(py_files),
        "personal_path_files_sample": personal[:20],
    }


def main() -> int:
    root = repo_root()
    inv = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "git_commit": "NO_GIT_REPOSITORY",
        "git_dirty": None,
        "pytest_collected": None,
        "directories": {n: _scan_dir(root, n) for n in KEY_DIRS},
        "required_for_artifact": [
            "brain/",
            "nexo/",
            "experiments/",
            "scripts/",
            "tests/",
            "configs/",
            "schemas/",
            "docs/",
            "roadmap/",
            "reports/",
        ],
    }
    try:
        inv["git_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, timeout=5
        ).strip()
        st = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True, timeout=5)
        inv["git_dirty"] = bool(st.strip())
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass
    try:
        out = subprocess.check_output(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/"],
            cwd=root,
            text=True,
            timeout=120,
        )
        for line in out.splitlines():
            if " tests collected" in line:
                inv["pytest_collected"] = int(line.strip().split()[0])
    except (subprocess.CalledProcessError, FileNotFoundError, OSError, ValueError):
        pass
    out_path = root / "reports" / "repository_inventory.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(inv, indent=2, ensure_ascii=False), encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
