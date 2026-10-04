"""
EngramCodec — compresión sparse int8 + zlib para engramas corticales.

Formato EGR1 (ensamble sparse) y EGRS (vector-resumen para índice SQLite).
Reduce ~2.7 KB/ensamble → ~150–400 B típicos.
"""

from __future__ import annotations

import struct
import zlib
from typing import Any

import numpy as np

MAGIC_SPARSE = b"EGR1"
MAGIC_SUMMARY = b"EGRS"
VERSION = 1

DEFAULT_TOP_K = 32


def _quantize_weights(weights: np.ndarray) -> tuple[np.ndarray, float]:
    w = np.asarray(weights, dtype=np.float32).ravel()
    if w.size == 0:
        return np.zeros(0, dtype=np.int8), 1.0
    scale = float(np.max(np.abs(w)))
    if scale < 1e-8:
        scale = 1.0
    w8 = np.clip(np.round(w / scale * 127.0), -127, 127).astype(np.int8)
    return w8, scale


def _dequantize_weights(w8: np.ndarray, scale: float) -> np.ndarray:
    if w8.size == 0:
        return np.zeros(0, dtype=np.float32)
    return (w8.astype(np.float32) / 127.0) * float(scale)


def encode_sparse(indices: np.ndarray, weights: np.ndarray) -> bytes:
    idx = np.asarray(indices, dtype=np.int32).ravel()
    w8, scale = _quantize_weights(weights)
    n = int(idx.size)
    payload = struct.pack("<If", n, scale) + idx.tobytes() + w8.tobytes()
    compressed = zlib.compress(payload, level=9)
    return MAGIC_SPARSE + bytes([VERSION]) + compressed


def decode_sparse(data: bytes) -> tuple[np.ndarray, np.ndarray]:
    if not data or data[:4] != MAGIC_SPARSE:
        raise ValueError("not EGR1 sparse blob")
    payload = zlib.decompress(data[5:])
    n, scale = struct.unpack("<If", payload[:8])
    n = int(n)
    if n <= 0:
        return np.zeros(0, dtype=np.int32), np.zeros(0, dtype=np.float32)
    idx = np.frombuffer(payload[8 : 8 + n * 4], dtype=np.int32).copy()
    w8 = np.frombuffer(payload[8 + n * 4 : 8 + n * 4 + n], dtype=np.int8)
    return idx, _dequantize_weights(w8, scale)


def encode_summary(vec: np.ndarray, *, dim: int, top_k: int = DEFAULT_TOP_K) -> bytes:
    """Resumen denso → sparse comprimido para SQLite."""
    v = np.asarray(vec, dtype=np.float32).ravel()
    if v.size < dim:
        v = np.pad(v, (0, dim - v.size))
    v = v[:dim]
    idx = np.flatnonzero(v > 0.02)
    if idx.size == 0:
        idx = np.array([int(np.argmax(v))], dtype=np.int32)
        weights = np.array([float(v[idx[0]])], dtype=np.float32)
    else:
        order = np.argsort(v[idx])[::-1][:top_k]
        idx = idx[order].astype(np.int32)
        weights = v[idx].astype(np.float32)
    inner = encode_sparse(idx, weights)
    return MAGIC_SUMMARY + bytes([VERSION]) + inner[len(MAGIC_SPARSE) + 1 :]


def decode_summary(blob: bytes, *, dim: int) -> np.ndarray | None:
    if not blob:
        return None
    if blob[:4] == MAGIC_SUMMARY:
        try:
            inner = MAGIC_SPARSE + bytes([VERSION]) + blob[5:]
            idx, weights = decode_sparse(inner)
            out = np.zeros(dim, dtype=np.float32)
            for i, w in zip(idx, weights):
                if 0 <= int(i) < dim:
                    out[int(i)] = max(out[int(i)], float(w))
            m = float(out.max())
            if m > 1e-6:
                out /= m
            return np.clip(out, 0.0, 1.0)
        except (ValueError, zlib.error, struct.error):
            return None
    expected = dim * 4
    if len(blob) == expected:
        return np.frombuffer(blob, dtype=np.float32).copy()
    return None


def expand_summary_to_dim(summary: np.ndarray, dim: int) -> np.ndarray:
    s = np.asarray(summary, dtype=np.float32).ravel()
    if s.size >= dim:
        return s[:dim]
    return np.pad(s, (0, dim - s.size))


def encode_chunk_pattern(pattern: np.ndarray) -> bytes:
    """Patrón de chunk connectoma → int8 + zlib."""
    p = np.asarray(pattern, dtype=np.float32).ravel()
    scale = float(np.max(np.abs(p))) or 1.0
    p8 = np.clip(np.round(p / scale * 127.0), -127, 127).astype(np.int8)
    payload = struct.pack("<If", p8.size, scale) + p8.tobytes()
    return b"EGCK" + bytes([VERSION]) + zlib.compress(payload, level=6)


def decode_chunk_pattern(data: bytes) -> np.ndarray | None:
    if not data or data[:4] != b"EGCK":
        return None
    try:
        payload = zlib.decompress(data[5:])
        n, scale = struct.unpack("<If", payload[:8])
        p8 = np.frombuffer(payload[8 : 8 + int(n)], dtype=np.int8)
        return _dequantize_weights(p8, scale)
    except (zlib.error, struct.error):
        return None


def estimate_sparse_bytes(n_units: int) -> int:
    """Estimación de tamaño en disco (sparse + overhead zlib)."""
    raw = 8 + n_units * 5
    return max(48, int(raw * 0.55) + 12)


def codec_stats(samples: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "format_sparse": "EGR1",
        "format_summary": "EGRS",
        "format_chunk": "EGCK",
        "version": VERSION,
        "typical_bytes_per_assembly": 320,
    }
