"""Captura de entorno de ejecución para reproducibilidad."""

from __future__ import annotations

import json
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nexo.paths import repo_root

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")


class GitProvenanceError(RuntimeError):
    """Raised when git commit/dirty state cannot be resolved."""


def git_commit() -> str:
    """Return the full 40-char HEAD SHA, or raise if git provenance is unavailable."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root(),
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except FileNotFoundError as exc:
        raise GitProvenanceError(
            "cannot resolve git commit: 'git' executable not found on PATH"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise GitProvenanceError("cannot resolve git commit: git rev-parse timed out") from exc
    except OSError as exc:
        raise GitProvenanceError(f"cannot resolve git commit: {exc}") from exc

    if out.returncode != 0:
        detail = (out.stderr or out.stdout or "").strip() or f"exit {out.returncode}"
        raise GitProvenanceError(f"cannot resolve git commit: git rev-parse HEAD failed: {detail}")

    commit = out.stdout.strip()
    if not _SHA1_RE.fullmatch(commit):
        raise GitProvenanceError(f"cannot resolve git commit: unexpected rev-parse output: {commit!r}")
    return commit


def git_dirty() -> bool:
    """Return whether the working tree has uncommitted changes; raise if git is unavailable."""
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root(),
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except FileNotFoundError as exc:
        raise GitProvenanceError(
            "cannot resolve dirty state: 'git' executable not found on PATH"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise GitProvenanceError("cannot resolve dirty state: git status timed out") from exc
    except OSError as exc:
        raise GitProvenanceError(f"cannot resolve dirty state: {exc}") from exc

    if out.returncode != 0:
        detail = (out.stderr or out.stdout or "").strip() or f"exit {out.returncode}"
        raise GitProvenanceError(f"cannot resolve dirty state: git status failed: {detail}")
    return bool(out.stdout.strip())


def capture_environment() -> dict[str, Any]:
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        # Anonymize machine-local paths; keep only the interpreter basename.
        "python_executable": Path(sys.executable).name,
        "platform": platform.platform(),
        "repo_root": "<REPO_ROOT>",
        "commit": git_commit(),
        "dirty_repository": git_dirty(),
    }


def write_environment_files(root: Path | None = None) -> Path:
    """Write ENVIRONMENT.json and COMMIT_HASH.txt. Fails loudly if git is unavailable."""
    root = root or repo_root()
    env = capture_environment()
    commit = env["commit"]
    if not _SHA1_RE.fullmatch(str(commit)):
        raise GitProvenanceError(f"refusing to write non-SHA commit sentinel: {commit!r}")
    (root / "ENVIRONMENT.json").write_text(
        json.dumps(env, indent=2) + "\n", encoding="utf-8"
    )
    (root / "COMMIT_HASH.txt").write_text(commit + "\n", encoding="utf-8")
    return root / "ENVIRONMENT.json"
