"""
Codificación multimodal → vectores sensoriales (sin modelos pesados).

Imagen: rejilla en escala de grises.
Documento: texto extraído (PDF).
Audio: bandas espectrales (WAV) o huella de bytes.
Texto: hash disperso.
"""

from __future__ import annotations

import hashlib
import io
import struct
import wave
from typing import BinaryIO

import numpy as np


def _fit(vec: np.ndarray, n: int) -> np.ndarray:
    out = np.zeros(n, dtype=np.float32)
    v = np.asarray(vec, dtype=np.float32).ravel()
    if v.size == 0:
        return out
    if v.size >= n:
        out[:] = v[:n]
    else:
        out[: v.size] = v
    m = float(out.max())
    if m > 1e-6:
        out /= m
    return out


def encode_text(text: str, n: int) -> np.ndarray:
    vec = np.zeros(n, dtype=np.float32)
    raw = (text or "").encode("utf-8") or b"\x00"
    for i, ch in enumerate(raw[:512]):
        base = (ch + i * 17) % n
        for k in range(3):
            vec[(base + k * 5) % n] = 1.0
    return _fit(vec, n)


def encode_bytes(data: bytes, n: int) -> np.ndarray:
    """Huella determinista para formatos no soportados."""
    vec = np.zeros(n, dtype=np.float32)
    for i in range(0, min(len(data), 4096), 4):
        chunk = data[i : i + 4]
        val = int.from_bytes(chunk.ljust(4, b"\x00"), "little", signed=False)
        vec[(val + i) % n] += 1.0
    return _fit(vec, n)


def encode_image(data: bytes, n: int) -> np.ndarray:
    try:
        from PIL import Image
    except ImportError:
        return encode_bytes(data, n)

    img = Image.open(io.BytesIO(data)).convert("L")
    side = int(np.ceil(np.sqrt(n)))
    img = img.resize((side, side), Image.Resampling.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return _fit(arr.ravel(), n)


def encode_pdf(data: bytes, n: int) -> np.ndarray:
    text_parts: list[str] = []
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        for page in reader.pages[:12]:
            t = page.extract_text() or ""
            text_parts.append(t)
    except Exception:
        return encode_bytes(data, n)
    text = "\n".join(text_parts).strip()
    if not text:
        return encode_bytes(data, n)
    return encode_text(text[:8000], n)


def encode_audio(data: bytes, n: int) -> np.ndarray:
    try:
        with wave.open(io.BytesIO(data), "rb") as wf:
            nch = wf.getnchannels()
            rate = wf.getframerate()
            frames = wf.readframes(wf.getnframes())
        samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
        if nch > 1:
            samples = samples.reshape(-1, nch).mean(axis=1)
        if samples.size < 64:
            return encode_bytes(data, n)
        # Energía por bandas (FFT liviana)
        chunk = samples[: min(samples.size, rate * 8)]
        spec = np.abs(np.fft.rfft(chunk))
        bands = np.array_split(spec, min(n, 32))
        vec = np.array([b.mean() for b in bands], dtype=np.float32)
        if vec.size < n:
            vec = np.pad(vec, (0, n - vec.size))
        return _fit(vec[:n], n)
    except Exception:
        return encode_bytes(data, n)


def encode_epub(data: bytes, n: int) -> np.ndarray:
    """Libro EPUB: extrae HTML/texto de capítulos (zip + XML)."""
    import re
    import zipfile

    text_parts: list[str] = []
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
                    text_parts.append(plain)
    except Exception:
        return encode_bytes(data, n)
    text = "\n".join(text_parts).strip()
    if not text:
        return encode_bytes(data, n)
    return encode_text(text[:12000], n)


def encode_file(data: bytes, filename: str, n: int) -> tuple[np.ndarray, str]:
    name = (filename or "").lower()
    if name.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")):
        return encode_image(data, n), "image"
    if name.endswith(".pdf"):
        return encode_pdf(data, n), "document"
    if name.endswith((".wav", ".wave")):
        return encode_audio(data, n), "audio"
    if name.endswith((".mp3", ".ogg", ".flac", ".m4a")):
        # Sin decoder pesado: metadatos + bytes
        mix = encode_bytes(data, n) + encode_text(name, n)
        return _fit(mix, n), "audio"
    if name.endswith((".txt", ".md", ".json", ".csv")):
        try:
            return encode_text(data.decode("utf-8", errors="replace")[:8000], n), "text"
        except Exception:
            pass
    if name.endswith(".epub"):
        return encode_epub(data, n), "document"
    # Heurística por contenido
    if data[:4] == b"%PDF":
        return encode_pdf(data, n), "document"
    if data[:2] in (b"\xff\xd8", b"\x89P"):
        return encode_image(data, n), "image"
    if data[:4] == b"RIFF" or data[:4] == b"FORM":
        return encode_audio(data, n), "audio"
    return encode_bytes(data, n), "text"


def stimulus_id(data: bytes, label: str) -> str:
    return hashlib.sha256(data + label.encode("utf-8")).hexdigest()[:16]
