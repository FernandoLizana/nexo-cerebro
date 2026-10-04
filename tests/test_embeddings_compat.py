"""Compatibility and hardening regressions for SemanticEmbedder."""

from __future__ import annotations

import numpy as np
import pytest

from brain.embeddings import SemanticEmbedder


def test_similarity_rejects_incompatible_dims() -> None:
    emb = SemanticEmbedder(use_ollama=False)
    a = np.zeros(8, dtype=np.float32)
    b = np.zeros(16, dtype=np.float32)
    assert not emb.compatible(a, b)
    with pytest.raises(ValueError, match="incompatible embedding dims"):
        emb.similarity(a, b)
    assert emb.last_error and "incompatible" in emb.last_error


def test_compatible_same_dims() -> None:
    emb = SemanticEmbedder(use_ollama=False)
    a = np.ones(4, dtype=np.float32)
    b = np.ones(4, dtype=np.float32)
    assert emb.compatible(a, b)
    assert emb.similarity(a, b) == pytest.approx(1.0)


def test_cache_key_differs_for_shared_512_prefix() -> None:
    emb = SemanticEmbedder(use_ollama=False)
    prefix = "x" * 512
    text_a = prefix + "ALPHA_UNIQUE_TAIL"
    text_b = prefix + "BETA_UNIQUE_TAIL"
    assert text_a[:512] == text_b[:512]
    key_a = emb._make_cache_key(
        text_a,
        backend="hash",
        model="hash-fallback",
        dim=emb.fallback_dim,
        mode="hash_fallback",
    )
    key_b = emb._make_cache_key(
        text_b,
        backend="hash",
        model="hash-fallback",
        dim=emb.fallback_dim,
        mode="hash_fallback",
    )
    # Old cache used text[:512] as the key and would collide here.
    assert key_a != key_b
    emb.embed(text_a)
    emb.embed(text_b)
    assert key_a in emb._cache and key_b in emb._cache
    assert len(emb._cache) >= 2


def test_fallback_mode_labeled() -> None:
    emb = SemanticEmbedder(use_ollama=False)
    vec = emb.embed("hello cerebro")
    assert vec.size == emb.fallback_dim
    assert emb.is_fallback is True
    st = emb.status()
    assert st["fallback"] is True
    assert st["is_fallback"] is True
    assert st["backend"] == "hash"
    assert st["mode"] == "hash_fallback"
    assert st["version"] == "hash_fallback"
    assert st["model_requested"] == emb.model
    assert st["model_used"] == "hash-fallback"
    assert st["dimension"] == emb.fallback_dim
    assert "cache_size" in st
    assert "last_error" in st


def test_embed_pin_refuses_substitution(monkeypatch) -> None:
    emb = SemanticEmbedder(use_ollama=True, model="exact-embed:v1")
    monkeypatch.setenv("CEREBRO_EMBED_PIN", "1")
    names = ["nomic-embed-text:latest", "mxbai-embed-large:latest"]
    assert emb._resolve_model(names) == ""
    assert "CEREBRO_EMBED_PIN" in emb.last_error
    monkeypatch.setenv("CEREBRO_EMBED_PIN", "0")
    # Without pin, substitution is allowed.
    resolved = emb._resolve_model(names)
    assert resolved in names
