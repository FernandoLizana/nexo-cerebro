#!/usr/bin/env python3
"""Extrae Brain Facts 2018 PDF → manifest JSON + copia a biblioteca."""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
PDF_DEFAULT = Path.home() / "Downloads" / "Brain Facts Book 2018 high res.pdf"
OUT = ROOT / "data" / "curriculum" / "brain_facts_manifest.json"
LIB = ROOT / "data" / "library"

CHAPTERS = [
    ("intro", "Introduction", 4, 9),
    ("brain_basics", "Brain Basics", 10, 17),
    ("senses", "Senses & Perception", 18, 25),
    ("movement", "Movement", 26, 31),
    ("learning_memory_emotion", "Learning, Memory & Emotions", 32, 37),
    ("thinking_language", "Thinking, Planning & Language", 38, 43),
    ("developing_brain", "The Developing Brain", 44, 48),
    ("child_adolescent", "Infant, Child & Adolescent Brain", 49, 52),
    ("adult_aging", "Adult & Aging Brain", 53, 58),
    ("brain_states", "Brain States", 59, 65),
    ("body_balance", "The Body in Balance", 66, 70),
    ("childhood_disorders", "Childhood Disorders", 71, 75),
    ("psychiatric", "Psychiatric Disorders", 76, 80),
    ("addiction", "Addiction", 81, 87),
    ("injury_illness", "Injury & Illness", 88, 95),
    ("neurodegenerative", "Neurodegenerative Diseases", 96, 104),
    ("research", "Kinds of Research", 105, 111),
    ("solving_problems", "Solving Human Problems", 112, 117),
    ("society", "Neuroscience in Society", 118, 121),
    ("glossary", "Glossary", 122, 127),
]

MODULE_MAP = {
    "intro": ["cortex", "thalamus", "hippocampus"],
    "brain_basics": ["cortex", "synapses", "glia", "thalamus"],
    "senses": ["thalamus", "sensory", "parietal", "amygdala"],
    "movement": ["motor", "basal_ganglia", "cerebellum", "spinal"],
    "learning_memory_emotion": ["hippocampus", "amygdala", "limbic", "basal_ganglia"],
    "thinking_language": ["prefrontal", "broca", "language", "executive"],
    "developing_brain": ["cortex", "hippocampus", "glia"],
    "child_adolescent": ["prefrontal", "limbic", "hypothalamus"],
    "adult_aging": ["hippocampus", "glia", "perfusion"],
    "brain_states": ["brainstem", "thalamus", "hypothalamus", "ventricles"],
    "body_balance": ["hypothalamus", "insula", "vagus", "autonomic", "pituitary"],
    "childhood_disorders": ["prefrontal", "basal_ganglia", "thalamus"],
    "psychiatric": ["amygdala", "prefrontal", "serotonin_network"],
    "addiction": ["basal_ganglia", "prefrontal", "dopamine_network"],
    "injury_illness": ["glia", "perfusion", "spinal"],
    "neurodegenerative": ["hippocampus", "glia", "perfusion"],
    "research": ["cortex", "hippocampus"],
    "solving_problems": ["prefrontal", "executive", "default_mode"],
    "society": ["language", "prefrontal"],
    "glossary": ["cortex"],
}


def main() -> int:
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else PDF_DEFAULT
    if not pdf.is_file():
        print(f"PDF no encontrado: {pdf}", file=sys.stderr)
        return 1

    LIB.mkdir(parents=True, exist_ok=True)
    dest = LIB / "Brain_Facts_Book_2018.pdf"
    if not dest.exists() or dest.stat().st_size != pdf.stat().st_size:
        shutil.copy2(pdf, dest)

    reader = PdfReader(str(pdf))
    pages = [re.sub(r"\s+", " ", (p.extract_text() or "")).strip() for p in reader.pages]

    def slice_pages(a: int, b: int) -> str:
        return " ".join(pages[a - 1 : b])

    chapters = []
    for key, title, start, end in CHAPTERS:
        text = slice_pages(start, end)
        chapters.append(
            {
                "key": key,
                "title": title,
                "page_start": start,
                "page_end": end,
                "modules": MODULE_MAP.get(key, []),
                "text": text[:12000],
                "preview": text[:280] + ("…" if len(text) > 280 else ""),
            }
        )

    manifest = {
        "source": "Brain Facts Book 2018 (SfN)",
        "library_path": "Brain_Facts_Book_2018.pdf",
        "total_pages": len(pages),
        "chapters": chapters,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK {OUT} ({len(chapters)} capítulos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
