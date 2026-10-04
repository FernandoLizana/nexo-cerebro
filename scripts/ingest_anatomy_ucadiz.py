#!/usr/bin/env python3
"""Extrae Anatomía Humana 2022 (UCadiz) PDF → manifest JSON + copia a biblioteca."""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
PDF_DEFAULT = Path.home() / "Downloads" / "Anatomia-Humana-2022-1.pdf"
OUT = ROOT / "data" / "curriculum" / "anatomy_humana_2022_manifest.json"
LIB = ROOT / "data" / "library"

# Capítulos del libro (páginas PDF 1-indexed)
SECTIONS = [
    (
        "morfologia_general",
        "Morfología general",
        1,
        5,
        18,
        ["osteology", "locomotor", "body_plan"],
    ),
    (
        "aparato_locomotor",
        "Generalidades del aparato locomotor",
        1,
        19,
        40,
        ["osteology", "arthrology", "myology", "locomotor"],
    ),
    (
        "ms_intro_osteologia",
        "Miembro superior — introducción y osteología",
        2,
        41,
        68,
        ["osteology", "humerus", "radius_ulna", "hand"],
    ),
    (
        "ms_articulaciones",
        "Miembro superior — articulaciones",
        2,
        69,
        95,
        ["arthrology", "shoulder", "elbow", "wrist"],
    ),
    (
        "ms_musculos",
        "Miembro superior — miología",
        2,
        96,
        118,
        ["myology", "brachial_plexus", "locomotor"],
    ),
    (
        "ms_angiologia",
        "Miembro superior — angiología y neurología",
        2,
        119,
        132,
        ["brachial_plexus", "arteries", "spinal"],
    ),
    (
        "mi_intro_osteologia",
        "Miembro inferior — introducción y osteología",
        3,
        133,
        158,
        ["osteology", "femur", "tibia", "foot"],
    ),
    (
        "mi_articulaciones",
        "Miembro inferior — articulaciones",
        3,
        159,
        188,
        ["arthrology", "hip", "knee", "ankle"],
    ),
    (
        "mi_musculos",
        "Miembro inferior — miología",
        3,
        189,
        215,
        ["myology", "locomotor", "lumbosacral"],
    ),
    (
        "mi_angiologia",
        "Miembro inferior — angiología y neurología",
        3,
        216,
        246,
        ["lumbosacral", "sciatic", "arteries", "nociception"],
    ),
]


def main() -> int:
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else PDF_DEFAULT
    if not pdf.is_file():
        print(f"PDF no encontrado: {pdf}", file=sys.stderr)
        return 1

    LIB.mkdir(parents=True, exist_ok=True)
    dest = LIB / "Anatomia_Humana_2022_UCadiz.pdf"
    if not dest.exists() or dest.stat().st_size != pdf.stat().st_size:
        shutil.copy2(pdf, dest)

    reader = PdfReader(str(pdf))
    pages = [re.sub(r"\s+", " ", (p.extract_text() or "")).strip() for p in reader.pages]

    def slice_pages(a: int, b: int) -> str:
        end = min(b, len(pages))
        start = max(1, a)
        return " ".join(pages[start - 1 : end])

    sections = []
    for key, title, chapter, start, end, anatomy in SECTIONS:
        text = slice_pages(start, end)
        sections.append(
            {
                "key": key,
                "title": title,
                "chapter": chapter,
                "page_start": start,
                "page_end": end,
                "anatomy": anatomy,
                "text": text[:12000],
                "preview": text[:280] + ("…" if len(text) > 280 else ""),
            }
        )

    manifest = {
        "source": "Anatomía Humana — Morfología General y Miembros (UCadiz 2022)",
        "library_path": "Anatomia_Humana_2022_UCadiz.pdf",
        "total_pages": len(pages),
        "sections": sections,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK {OUT} ({len(sections)} secciones)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
