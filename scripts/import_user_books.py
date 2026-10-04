"""Importa PDFs del usuario a data/library/ y opcionalmente verifica extracción."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from brain.library import ensure_library, list_books
from brain.text_extract import extract_plain_text


def import_paths(paths: list[Path], *, dry_run: bool = False) -> list[dict]:
    lib = ensure_library()
    out: list[dict] = []
    for src in paths:
        if not src.is_file():
            print(f"skip (no file): {src}")
            continue
        dest = lib / src.name
        if dry_run:
            print(f"would copy: {src} -> {dest}")
            out.append({"src": str(src), "dest": str(dest), "dry_run": True})
            continue
        if not dest.exists() or dest.stat().st_size != src.stat().st_size:
            shutil.copy2(src, dest)
        data = dest.read_bytes()
        text = extract_plain_text(data, dest.name)
        row = {"path": dest.relative_to(lib).as_posix(), "chars": len(text.strip())}
        out.append(row)
        print(f"ok: {row['path']} ({row['chars']} chars)")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Import user PDFs into cerebro library")
    parser.add_argument("files", nargs="+", help="PDF/EPUB paths to copy")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    import_paths([Path(p) for p in args.files], dry_run=args.dry_run)
    print(f"library now has {len(list_books())} books")


if __name__ == "__main__":
    main()
