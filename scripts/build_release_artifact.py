#!/usr/bin/env python3
"""Genera ZIP reproducible con validación previa y posterior."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "0.3.0"
SCRIPT_VERSION = "2.0.0"

EXCLUDED_DIRECTORY_NAMES = frozenset({
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "artifacts",
    "pack_gpt_adaptive_behavior",
    "publication_finalization",
    "publication_evidence",
})

EXCLUDED_RELATIVE_PREFIXES = (
    "data/brain_state/",
    "data/node_shelf/",
    "data/presence_hub/",
    "data/nexo_node/",
    "data/nexo_dashboard/",
    "data/lab_gateway/",
    "data/nexo_lab_gateway/",
    "data/world3d/",
    # Third-party / redistributable PDFs under data/library/ — see docs/NEXO_THIRD_PARTY_CONTENT.md
    "data/library/",
    "experiments/results/",
    "apps/android-node/app/build/",
    "apps/android-node/.gradle/",
    "scripts/_patch_artifact.py",
)

EXCLUDED_FILE_SUFFIXES = frozenset({
    ".pyc",
    ".pyo",
    ".log",
    ".tmp",
    ".rar",
    ".apk",
    ".aab",
    ".keystore",
    ".jks",
    ".pem",
    ".key",
    # Never ship third-party PDFs in the public GitHub artifact by default.
    ".pdf",
})

SECRET_NAME_MARKERS = (
    ".env",
    "credentials",
    "secret",
    "private_key",
    "pairing",
    "id_ed25519",
    "tls.key",
    "dashboard_token",
    "token.txt",
)

# Generic home/lab path markers (no machine-specific usernames).
PERSONAL_PATH_MARKERS = frozenset({
    "OneDrive",
    "Escritorio/cerebro",
    "Escritorio\\cerebro",
})
PERSONAL_PATH_REGEX = re.compile(
    r"(?i)(?:^|[^\w])(?:Users|home)[/\\][^/\\\s\"']+",
)

REQUIRED_PATHS = (
    "brain",
    "nexo",
    "experiments",
    "scripts",
    "tests",
    "configs",
    "schemas",
    "docs",
    "roadmap",
    "reports",
    "README.md",
    "README_REPRODUCCION.md",
    "pyproject.toml",
    "requirements.txt",
    "requirements-lock.txt",
    "CITATION.cff",
    "LICENSE",
    "CHANGELOG.md",
    "KNOWN_LIMITATIONS.md",
)

REQUIRED_PREFIXES = ("brain/", "nexo/", "experiments/", "tests/", "data/curriculum/")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _git_commit() -> str:
    from nexo.environment import git_commit

    return git_commit()


def _git_dirty() -> bool:
    from nexo.environment import git_dirty

    return git_dirty()


def validate_required_paths(root: Path) -> list[str]:
    missing = []
    for rel in REQUIRED_PATHS:
        if not (root / rel).exists():
            missing.append(rel)
    return missing


def _relative_parts(path: Path, root: Path) -> tuple[str, ...]:
    return path.relative_to(root).parts


def _should_exclude_dir(rel_parts: tuple[str, ...]) -> bool:
    return any(part in EXCLUDED_DIRECTORY_NAMES for part in rel_parts)


def _file_has_personal_content(path: Path, rel: str) -> bool:
    """Excluye resultados con rutas absolutas personales, no documentos de auditoría."""
    if rel.startswith(("reports/", "docs/")) and path.suffix in {".md", ".json"}:
        if "AUDIT" in path.name.upper() or "inventory" in path.name.lower():
            return False
    if not rel.startswith(("experiments/results/", "publication_", "artifacts/")):
        if path.suffix not in {".json", ".jsonl", ".csv"}:
            return False
    if path.suffix not in {".py", ".md", ".json", ".yaml", ".yml", ".txt", ".cff", ".toml", ".csv", ".jsonl"}:
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return any(marker in text for marker in PERSONAL_PATH_MARKERS) or bool(
        PERSONAL_PATH_REGEX.search(text)
    )


def collect_files(root: Path) -> tuple[list[tuple[Path, str]], list[str], int]:
    included: list[tuple[Path, str]] = []
    excluded_reasons: list[str] = []
    excluded_count = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = _relative_parts(path, root)
        if _should_exclude_dir(rel_parts):
            excluded_count += 1
            continue
        if path.suffix.lower() in EXCLUDED_FILE_SUFFIXES:
            excluded_count += 1
            continue
        if path.stat().st_size > 50_000_000:
            excluded_count += 1
            excluded_reasons.append(f"too_large:{path.relative_to(root).as_posix()}")
            continue
        rel = path.relative_to(root).as_posix()
        if any(rel.startswith(p) for p in EXCLUDED_RELATIVE_PREFIXES):
            excluded_count += 1
            continue
        low = rel.lower()
        if any(marker in low for marker in SECRET_NAME_MARKERS):
            excluded_count += 1
            excluded_reasons.append(f"secret_name:{rel}")
            continue
        if path.name in {".env", "local.properties", "keystore.properties"}:
            excluded_count += 1
            excluded_reasons.append(f"secret_file:{rel}")
            continue
        if _file_has_personal_content(path, rel):
            excluded_count += 1
            excluded_reasons.append(f"personal_content:{rel}")
            continue
        included.append((path, rel))
    return included, excluded_reasons, excluded_count


def scan_artifact_for_secrets(zf: zipfile.ZipFile) -> list[str]:
    hits: list[str] = []
    for name in zf.namelist():
        low = name.lower()
        if any(marker in low for marker in SECRET_NAME_MARKERS):
            hits.append(f"name:{name}")
            continue
        if name.endswith((".env", ".pem", ".key", ".keystore", ".jks")):
            hits.append(f"suffix:{name}")
        if low.endswith(".pdf") or low.startswith("data/library/"):
            hits.append(f"third_party_pdf_or_library:{name}")
    return hits


def _required_path_present(names: list[str], req: str) -> bool:
    if req.endswith("/"):
        prefix = req
        return any(n.startswith(prefix) or n == prefix.rstrip("/") for n in names)
    if "." not in Path(req).name:
        prefix = f"{req}/"
        return any(n.startswith(prefix) or n == req for n in names)
    return req in names


def validate_zip_contents(zf: zipfile.ZipFile) -> tuple[list[str], list[str], dict[str, bool]]:
    names = zf.namelist()
    errors: list[str] = []
    personal: list[str] = []
    if not names:
        errors.append("zip_empty")
    required_status: dict[str, bool] = {}
    for req in REQUIRED_PATHS:
        ok = _required_path_present(names, req)
        required_status[req] = ok
        if not ok:
            errors.append(f"missing_required:{req}")
    for prefix in REQUIRED_PREFIXES:
        if not any(n.startswith(prefix) for n in names):
            errors.append(f"missing_prefix:{prefix}")
    for n in names:
        if any(m.lower() in n.lower() for m in ("__pycache__", ".pytest_cache")):
            errors.append(f"cache_in_zip:{n}")
        if n.endswith(".pyc"):
            errors.append(f"pyc_in_zip:{n}")
        if n.startswith(("scripts/build_release_artifact.py", "scripts/generate_repository_inventory.py",
                           "scripts/verify_packaged_artifact.py", "reports/", "docs/")):
            continue
        if not n.endswith((".py", ".md", ".json", ".yaml", ".yml", ".txt", ".csv", ".jsonl")):
            continue
        try:
            data = zf.read(n)[:8000].decode("utf-8", errors="replace")
            if any(m in data for m in PERSONAL_PATH_MARKERS) or PERSONAL_PATH_REGEX.search(data):
                personal.append(n)
        except Exception:
            pass
    if personal:
        errors.append(f"personal_paths_in_zip:{len(personal)}")
    return errors, personal, required_status


def build(version: str = VERSION) -> Path:
    root = repo_root()
    missing = validate_required_paths(root)
    if missing:
        raise SystemExit(f"Faltan rutas obligatorias para empaquetar: {missing}")

    included, excluded_reasons, excluded_count = collect_files(root)
    if not included:
        raise SystemExit("No hay archivos para empaquetar (ZIP vacío).")

    dist = root / "dist"
    dist.mkdir(exist_ok=True)
    artifact_name = f"NEXO_REPRODUCIBLE_{version}.zip"
    out = dist / artifact_name
    if out.exists():
        out.unlink()

    total_bytes = 0
    rel_paths: list[str] = []
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, rel in included:
            zf.write(path, rel)
            total_bytes += path.stat().st_size
            rel_paths.append(rel)

    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    with zipfile.ZipFile(out, "r") as zf:
        zip_errors, personal, req_status = validate_zip_contents(zf)
        secret_hits = scan_artifact_for_secrets(zf)
    if secret_hits:
        zip_errors.append(f"secrets_in_zip:{len(secret_hits)}")
    if zip_errors:
        out.unlink(missing_ok=True)
        raise SystemExit(f"Validación posterior falló: {zip_errors[:10]}")

    manifest: dict[str, Any] = {
        "artifact_name": artifact_name,
        "version": version,
        "sha256": digest,
        "source_commit": _git_commit(),
        "source_dirty": _git_dirty(),
        "file_count": len(rel_paths),
        "total_uncompressed_bytes": total_bytes,
        "required_paths": req_status,
        "excluded_files_count": excluded_count,
        "excluded_samples": excluded_reasons[:30],
        "warnings": [],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script_version": SCRIPT_VERSION,
    }
    (dist / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (dist / "SHA256SUMS.txt").write_text(f"{digest}  {artifact_name}\n", encoding="utf-8")
    (dist / "ARTIFACT_CONTENTS.md").write_text(
        "\n".join([
            f"# {artifact_name}",
            "",
            f"- SHA256: `{digest}`",
            f"- Archivos: {len(rel_paths)}",
            f"- Commit: {_git_commit()}",
            "",
            "## Prefijos obligatorios",
            "",
            *[f"- `{p}` presente" for p in REQUIRED_PREFIXES],
        ]),
        encoding="utf-8",
    )
    return out


if __name__ == "__main__":
    p = build()
    print(p)
