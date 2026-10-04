"""Materials people leave on a node. Held until the central chooses them.

Text, PDF and images are stored. Nothing here is executed.
"""

from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def _shelf() -> Path:
    override = os.environ.get("NEXO_NODE_SHELF", "").strip()
    return Path(override) if override else ROOT / "data" / "node_shelf"
NODE_SOURCES = frozenset({"rama", "rama-b", "android-cerebro", "android-nodo"})
MAX_BYTES = 2_500_000
SUFFIXES = {
    ".txt": "text",
    ".md": "text",
    ".csv": "text",
    ".pdf": "pdf",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
    ".gif": "image",
}


def accept(source: str, name: str, data: bytes = b"", note: str = "") -> dict:
    source = str(source or "").strip()
    if source not in NODE_SOURCES:
        return {"ok": False, "error": "only nodes accept material"}
    raw_name = Path(str(name or "nota.txt")).name
    if not raw_name or raw_name in {".", ".."}:
        return {"ok": False, "error": "bad name"}
    suffix = Path(raw_name).suffix.lower()
    note = str(note or "").strip()[:500]
    if not data and note:
        data = note.encode("utf-8")
        if not suffix:
            raw_name = "nota.txt"
            suffix = ".txt"
    kind = SUFFIXES.get(suffix)
    if kind is None:
        return {"ok": False, "error": "only text, pdf or image"}
    if not data or len(data) > MAX_BYTES:
        return {"ok": False, "error": "empty or too large"}
    excerpt = _excerpt(kind, data, note)
    shelf = _shelf()
    shelf.mkdir(parents=True, exist_ok=True)
    item_id = _id_for(source, raw_name)
    record = {
        "id": item_id,
        "source": source,
        "name": raw_name,
        "kind": kind,
        "note": note,
        "status": "held",
        "chars": len(excerpt),
    }
    (shelf / f"{item_id}.json").write_text(json.dumps(record), encoding="utf-8")
    (shelf / f"{item_id}.txt").write_text(excerpt, encoding="utf-8")
    (shelf / f"{item_id}.bin").write_bytes(data)
    return {"ok": True, "item": record}


def list_held() -> list[dict]:
    shelf = _shelf()
    if not shelf.exists():
        return []
    rows = []
    for path in sorted(shelf.glob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if row.get("status") == "held":
            rows.append(row)
    return rows


def decode_b64(payload: str) -> bytes:
    raw = re.sub(r"\s+", "", str(payload or ""))
    if not raw:
        return b""
    return base64.b64decode(raw, validate=False)


PDF_HEADER = "PDF dejado en el nodo."


def split_excerpt(text: str) -> tuple[str, str]:
    """Header line, then the file body. The body is what may enter memory."""
    raw = str(text or "").replace("\r\n", "\n")
    if raw.startswith(PDF_HEADER):
        return PDF_HEADER, raw[len(PDF_HEADER):].strip()
    lines = raw.split("\n", 1)
    if len(lines) == 2 and lines[0].strip() in {PDF_HEADER, "PDF sin texto extraíble. Queda guardado, no ejecutado."}:
        return lines[0].strip(), lines[1].strip()
    return "", raw.strip()


def _excerpt(kind: str, data: bytes, note: str) -> str:
    if kind == "text":
        body = data.decode("utf-8", errors="replace").strip()
        return (note + "\n" + body).strip()[:8000]
    if kind == "pdf":
        body = _pdf_text(data)
        if not body:
            body = "PDF sin texto extraíble. Queda guardado, no ejecutado."
        return f"{PDF_HEADER}\n{body}".strip()[:8000]
    caption = note or "imagen sin nota"
    return f"Imagen dejada en el nodo. Nota de quien la dejó: {caption}"[:8000]


def _pdf_text(data: bytes) -> str:
    try:
        from pypdf import PdfReader
        import io

        reader = PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages[:8]:
            pages.append(page.extract_text() or "")
        return "\n".join(pages).strip()
    except Exception:
        return ""


def _id_for(source: str, name: str) -> str:
    import hashlib

    digest = hashlib.sha256(f"{source}|{name}".encode("utf-8")).hexdigest()[:16]
    return f"{source}-{digest}"
