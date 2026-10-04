"""Extrae texto plano de archivos para aprendizaje."""

from __future__ import annotations

import io
import os
import re
import zipfile


def extract_plain_text(data: bytes, filename: str = "", *, max_pages: int = 40) -> str:
    name = (filename or "").lower()
    if name.endswith((".txt", ".md", ".json", ".csv")):
        return data.decode("utf-8", errors="replace")
    if name.endswith(".pdf") or data[:4] == b"%PDF":
        text = _pdf_text(data, max_pages=max_pages)
        if len(text.strip()) < 80 and _ocr_enabled():
            ocr = _pdf_ocr(data, max_pages=min(max_pages, 8))
            if ocr.strip():
                return ocr
        return text
    if name.endswith(".epub"):
        return _epub_text(data)
    try:
        return data.decode("utf-8", errors="replace")
    except Exception:
        return ""


def _ocr_enabled() -> bool:
    return os.environ.get("CEREBRO_PDF_OCR", "0").strip().lower() in ("1", "true", "on", "yes")


def _pdf_text(data: bytes, *, max_pages: int = 40) -> str:
    text = _pdf_text_pymupdf(data, max_pages=max_pages)
    if len(text.strip()) >= 80:
        return text
    fallback = _pdf_text_pypdf(data, max_pages=max_pages)
    if len(fallback.strip()) > len(text.strip()):
        return fallback
    return text or fallback


def _pdf_text_pymupdf(data: bytes, *, max_pages: int = 40) -> str:
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=data, filetype="pdf")
        parts: list[str] = []
        for i in range(min(len(doc), max_pages)):
            parts.append(doc.load_page(i).get_text("text") or "")
        doc.close()
        return "\n".join(parts).strip()
    except Exception:
        return ""


def _pdf_text_pypdf(data: bytes, *, max_pages: int = 40) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        parts = [(page.extract_text() or "") for page in reader.pages[:max_pages]]
        return "\n".join(parts).strip()
    except Exception:
        return ""


def _pdf_ocr(data: bytes, *, max_pages: int = 8) -> str:
    ocr = _pdf_ocr_tesseract(data, max_pages=max_pages)
    if len(ocr.strip()) >= 80:
        return ocr
    return _pdf_ocr_easyocr(data, max_pages=max_pages)


def _pdf_ocr_tesseract(data: bytes, *, max_pages: int = 8) -> str:
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=data, filetype="pdf")
        parts: list[str] = []
        for i in range(min(len(doc), max_pages)):
            pix = doc.load_page(i).get_pixmap(dpi=180)
            img_bytes = pix.tobytes("png")
            parts.append(_ocr_image_bytes(img_bytes))
        doc.close()
        return "\n".join(p for p in parts if p).strip()
    except Exception:
        return ""


def _pdf_ocr_easyocr(data: bytes, *, max_pages: int = 6) -> str:
    try:
        import io

        import easyocr
        import fitz
        from PIL import Image

        reader = easyocr.Reader(["es", "en"], gpu=False, verbose=False)
        doc = fitz.open(stream=data, filetype="pdf")
        parts: list[str] = []
        for i in range(min(len(doc), max_pages)):
            pix = doc.load_page(i).get_pixmap(dpi=150)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            lines = reader.readtext(buf.getvalue(), detail=0, paragraph=True)
            text = "\n".join(str(x).strip() for x in lines if str(x).strip())
            if text:
                parts.append(text)
        doc.close()
        return "\n\n".join(parts).strip()
    except Exception:
        return ""


def _ocr_image_bytes(img_bytes: bytes) -> str:
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(io.BytesIO(img_bytes))
        return pytesseract.image_to_string(img, lang="spa+eng")
    except Exception:
        return ""


def _epub_text(data: bytes) -> str:
    parts: list[str] = []
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for name in sorted(zf.namelist()):
                if not name.lower().endswith((".xhtml", ".html", ".htm", ".xml", ".txt")):
                    continue
                if name.startswith("META-INF/"):
                    continue
                try:
                    raw = zf.read(name).decode("utf-8", errors="replace")
                except Exception:
                    continue
                plain = re.sub(r"<[^>]+>", " ", raw)
                plain = re.sub(r"\s+", " ", plain).strip()
                if plain:
                    parts.append(plain)
    except Exception:
        return ""
    return "\n".join(parts).strip()
