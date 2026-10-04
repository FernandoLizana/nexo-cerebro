"""Tests EngramCodec — compresión EGR1/EGRS/EGCK."""

from __future__ import annotations

import numpy as np

from brain.engram_codec import (
    decode_chunk_pattern,
    decode_sparse,
    decode_summary,
    encode_chunk_pattern,
    encode_sparse,
    encode_summary,
    estimate_sparse_bytes,
)


def test_encode_decode_sparse_roundtrip():
    idx = np.array([0, 5, 12, 99], dtype=np.int32)
    w = np.array([0.8, -0.3, 0.15, 0.5], dtype=np.float32)
    blob = encode_sparse(idx, w)
    assert blob[:4] == b"EGR1"
    idx2, w2 = decode_sparse(blob)
    assert np.array_equal(idx, idx2)
    assert np.allclose(w, w2, atol=0.02)


def test_encode_decode_summary_roundtrip():
    dim = 64
    vec = np.zeros(dim, dtype=np.float32)
    vec[[3, 7, 21]] = [0.9, 0.4, 0.6]
    blob = encode_summary(vec, dim=dim)
    assert blob[:4] == b"EGRS"
    out = decode_summary(blob, dim=dim)
    assert out is not None
    assert out.shape == (dim,)
    assert out[3] > 0.5
    assert out[7] > 0.2


def test_legacy_summary_bytes_still_decode():
    dim = 32
    vec = np.linspace(0, 1, dim, dtype=np.float32)
    out = decode_summary(vec.tobytes(), dim=dim)
    assert out is not None
    assert np.allclose(out, vec)


def test_chunk_pattern_codec():
    p = np.random.default_rng(1).normal(0, 0.2, size=128).astype(np.float32)
    blob = encode_chunk_pattern(p)
    assert blob[:4] == b"EGCK"
    out = decode_chunk_pattern(blob)
    assert out is not None
    assert np.allclose(p, out, atol=0.02)


def test_estimate_sparse_bytes_reasonable():
    est = estimate_sparse_bytes(32)
    assert 48 <= est <= 400
