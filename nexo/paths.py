"""Rutas del repositorio sin dependencias de rutas absolutas del usuario."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT: Path | None = None


def repo_root() -> Path:
    global _REPO_ROOT
    if _REPO_ROOT is None:
        _REPO_ROOT = Path(__file__).resolve().parent.parent
    return _REPO_ROOT


def reports_dir() -> Path:
    d = repo_root() / "reports"
    d.mkdir(parents=True, exist_ok=True)
    return d


def configs_dir() -> Path:
    return repo_root() / "configs"


def results_dir() -> Path:
    d = repo_root() / "results"
    d.mkdir(parents=True, exist_ok=True)
    return d


def schemas_dir() -> Path:
    return repo_root() / "schemas"
