"""
Biblioteca en disco: explorar y agregar libros al escritorio de Nexo.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

ALLOWED_SUFFIXES = {".pdf", ".epub", ".txt", ".md", ".doc", ".docx"}
_DEFAULT_LIBRARY_DIR = Path(__file__).resolve().parent.parent / "data" / "library"


def library_dir() -> Path:
    """Resolve the on-disk library root.

    Honours ``CEREBRO_LIBRARY_DIR`` so the test suite can point at an empty
    tree and never parse the user's local PDFs during sleep-study ticks.
    """
    override = os.environ.get("CEREBRO_LIBRARY_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    return _DEFAULT_LIBRARY_DIR


# Back-compat alias; prefer library_dir() when the env may change at runtime.
LIBRARY_DIR = _DEFAULT_LIBRARY_DIR


def ensure_library() -> Path:
    root = library_dir()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_path(rel: str) -> Path | None:
    base = ensure_library().resolve()
    target = (base / rel).resolve()
    if not str(target).startswith(str(base)):
        return None
    return target


def list_books() -> list[dict]:
    """Lista archivos de la biblioteca (solo extensiones permitidas)."""
    root = ensure_library()
    out: list[dict] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            continue
        rel = path.relative_to(root).as_posix()
        stat = path.stat()
        out.append(
            {
                "path": rel,
                "name": path.name,
                "size": stat.st_size,
                "ext": path.suffix.lower(),
            }
        )
    return out


def read_book(rel_path: str) -> tuple[bytes, str]:
    target = _safe_path(rel_path)
    if not target or not target.is_file():
        raise FileNotFoundError(f"Libro no encontrado: {rel_path}")
    if target.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValueError(f"Formato no permitido: {target.suffix}")
    return target.read_bytes(), target.name


def import_file(data: bytes, filename: str) -> dict:
    """Copia un archivo subido a data/library/."""
    name = Path(filename).name
    suffix = Path(name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError(f"Formato no permitido: {suffix}")
    dest = ensure_library() / name
    if dest.exists():
        stem, ext = dest.stem, dest.suffix
        n = 2
        while dest.exists():
            dest = ensure_library() / f"{stem}_{n}{ext}"
            n += 1
    dest.write_bytes(data)
    rel = dest.relative_to(ensure_library()).as_posix()
    return {"path": rel, "name": dest.name, "size": dest.stat().st_size}
