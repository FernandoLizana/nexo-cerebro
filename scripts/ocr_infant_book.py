"""OCR del libro infantil y actualización del currículo infant_brain."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from brain.library import ensure_library
from brain.text_extract import extract_plain_text

PDF_NAME = "Mi-primer-libro-del-cerebro.pdf"
SECTIONS_PATH = ROOT / "data" / "curriculum" / "infant_brain" / "sections.json"
EXTRACT_PATH = ensure_library() / "_extract_cerebro_infantil.txt"

# Temas infantiles esperados → claves del currículo
TOPIC_HINTS: list[tuple[str, str, str]] = [
    ("cerebro_cuerpo", "Tu cerebro manda en tu cuerpo", r"cuerpo|mover|múscul|hablar"),
    ("neuronas_mensajeras", "Neuronas mensajeras", r"neurona|mensaj|señal|eléctric"),
    ("cinco_sentidos", "Los cinco sentidos", r"sentido|ver|oír|oir|tocar|gust|olfat"),
    ("emociones", "Emociones", r"emoci|alegr|miedo|cari|trist|enoj"),
    ("dormir_aprender", "Dormir para aprender", r"dorm|sueñ|aprend|repas"),
    ("proteger_cerebro", "Protege tu cerebro", r"proteg|casco|salud|descans|comida"),
]


def _tesseract_path() -> str | None:
    env = os.environ.get("TESSERACT_CMD", "").strip()
    if env and Path(env).is_file():
        return env
    for candidate in (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ):
        if Path(candidate).is_file():
            return candidate
    return None


def ocr_pdf_tesseract(data: bytes, *, max_pages: int = 24) -> str:
    import fitz
    import pytesseract
    from PIL import Image

    cmd = _tesseract_path()
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd
    doc = fitz.open(stream=data, filetype="pdf")
    parts: list[str] = []
    for i in range(min(len(doc), max_pages)):
        pix = doc.load_page(i).get_pixmap(dpi=200)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        text = pytesseract.image_to_string(img, lang="spa+eng")
        if text.strip():
            parts.append(f"--- page {i + 1} ---\n{text.strip()}")
    doc.close()
    return "\n\n".join(parts)


def ocr_pdf_easyocr(data: bytes, *, max_pages: int = 12) -> str:
    import io

    import easyocr
    import fitz
    from PIL import Image

    reader = easyocr.Reader(["es", "en"], gpu=False, verbose=False)
    doc = fitz.open(stream=data, filetype="pdf")
    parts: list[str] = []
    for i in range(min(len(doc), max_pages)):
        pix = doc.load_page(i).get_pixmap(dpi=160)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        lines = reader.readtext(buf.getvalue(), detail=0, paragraph=True)
        text = "\n".join(str(x).strip() for x in lines if str(x).strip())
        if text:
            parts.append(f"--- page {i + 1} ---\n{text}")
    doc.close()
    return "\n\n".join(parts)


def extract_infant_text(pdf_path: Path, *, max_pages: int = 24) -> str:
    data = pdf_path.read_bytes()
    plain = extract_plain_text(data, pdf_path.name, max_pages=max_pages)
    if len(plain.strip()) >= 120:
        return plain
    os.environ.setdefault("CEREBRO_PDF_OCR", "1")
    if _tesseract_path():
        try:
            ocr = ocr_pdf_tesseract(data, max_pages=max_pages)
            if len(ocr.strip()) >= 80:
                return ocr
        except Exception as exc:
            print(f"tesseract OCR failed: {exc}")
    try:
        print("Trying EasyOCR (first run downloads models)…")
        ocr = ocr_pdf_easyocr(data, max_pages=min(max_pages, 12))
        if ocr.strip():
            return ocr
    except Exception as exc:
        print(f"EasyOCR failed: {exc}")
    return plain


def _pick_snippet(full: str, pattern: str, fallback: str) -> str:
    chunks = re.split(r"--- page \d+ ---", full)
    chunks = [c.strip() for c in chunks if c.strip()]
    rx = re.compile(pattern, re.I)
    for chunk in chunks:
        if rx.search(chunk):
            lines = [ln.strip() for ln in chunk.splitlines() if len(ln.strip()) > 8]
            if lines:
                return " ".join(lines[:4])[:420]
    return fallback


def update_sections(full_text: str) -> list[dict]:
    sections = json.loads(SECTIONS_PATH.read_text(encoding="utf-8"))
    for sec in sections:
        key = sec["key"]
        hint = next((h for h in TOPIC_HINTS if h[0] == key), None)
        if not hint:
            continue
        _, title, pattern = hint
        snippet = _pick_snippet(full_text, pattern, sec.get("teaching", ""))
        sec["teaching"] = snippet
        sec["library_path"] = PDF_NAME
        sec["title"] = title
    return sections


def main() -> None:
    pdf = ensure_library() / PDF_NAME
    if not pdf.is_file():
        raise SystemExit(f"Missing PDF: {pdf}")
    print(f"OCR/extract: {pdf.name}")
    text = extract_infant_text(pdf, max_pages=24)
    EXTRACT_PATH.write_text(text, encoding="utf-8")
    print(f"Saved extract: {EXTRACT_PATH} ({len(text.strip())} chars)")
    sections = update_sections(text)
    SECTIONS_PATH.write_text(json.dumps(sections, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated curriculum: {SECTIONS_PATH}")
    for s in sections:
        prev = (s.get("teaching") or "")[:72]
        print(f"  {s['n']}. {s['title']}: {prev}…")


if __name__ == "__main__":
    main()
