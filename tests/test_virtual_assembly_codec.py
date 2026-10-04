"""Tests VirtualAssemblyStore con codec EGR1."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np

from brain.virtual_assembly import VirtualAssemblyStore


def test_virtual_assembly_egm_save_load():
    with tempfile.TemporaryDirectory() as tmp:
        store = VirtualAssemblyStore(
            Path(tmp),
            pattern_dim=64,
            neurons_per_assembly=20,
            hot_size=4,
            recall_k=3,
        )
        idx = np.array([1, 4, 8, 16], dtype=np.int32)
        w = np.array([0.5, 0.3, -0.2, 0.9], dtype=np.float32)
        key = store._save_sparse("testkey", idx, w)
        assert key.endswith(".egm")
        loaded = store._load_sparse("testkey")
        assert loaded is not None
        idx2, w2 = loaded
        assert np.array_equal(idx, idx2)
        assert np.allclose(w, w2, atol=0.02)
        store.close()


def test_virtual_assembly_summary_codec():
    with tempfile.TemporaryDirectory() as tmp:
        store = VirtualAssemblyStore(Path(tmp), pattern_dim=32)
        vec = np.zeros(32, dtype=np.float32)
        vec[5] = 0.8
        vec[11] = 0.4
        blob = store._encode_summary(vec)
        out = store._decode_summary(blob)
        assert out is not None
        assert out[5] > 0.5
        store.close()
