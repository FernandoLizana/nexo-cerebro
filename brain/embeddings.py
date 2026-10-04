"""
Embeddings semánticos vía Ollama para recall y memoria de trabajo.

Fallback: huella hash normalizada si Ollama no está disponible.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from collections import OrderedDict
from dataclasses import dataclass, field

import numpy as np

from .encode import encode_text

_CACHE_MAX = 512


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na < 1e-6 or nb < 1e-6:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _is_embedding_model(name: str) -> bool:
    base = name.split(":")[0].lower()
    markers = (
        "embed",
        "nomic-embed",
        "mxbai-embed",
        "all-minilm",
        "snowflake-arctic-embed",
        "bge-",
        "gte-",
    )
    return any(m in base for m in markers)


def _normalize(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n < 1e-6:
        return v
    return (v / n).astype(np.float32)


@dataclass
class SemanticEmbedder:
    use_ollama: bool = field(
        default_factory=lambda: _env_bool("CEREBRO_EMBED_OLLAMA", False)
    )
    base_url: str = field(
        default_factory=lambda: os.environ.get(
            "CEREBRO_OLLAMA_URL", "http://127.0.0.1:11434"
        ).rstrip("/")
    )
    model: str = field(
        default_factory=lambda: os.environ.get(
            "CEREBRO_EMBED_MODEL", "nomic-embed-text:latest"
        )
    )
    fallback_dim: int = 384
    timeout_s: float = 12.0
    available: bool = field(default=False, init=False)
    resolved_model: str = field(default="", init=False)
    last_error: str = field(default="", init=False)
    embedding_dim: int = field(default=0, init=False)
    is_fallback: bool = field(default=True, init=False)
    _cache: OrderedDict[str, np.ndarray] = field(
        default_factory=OrderedDict, init=False
    )

    def __post_init__(self) -> None:
        if self.use_ollama:
            self.available = self.ping()
            self.is_fallback = not self.available
        else:
            self.available = False
            self.is_fallback = True
            self.embedding_dim = self.fallback_dim

    def _backend_label(self) -> str:
        if self.use_ollama and self.available and not self.is_fallback:
            return "ollama"
        return "hash"

    def _mode_label(self) -> str:
        if self.use_ollama and self.available and not self.is_fallback:
            return "ollama"
        return "hash_fallback"

    def _active_model(self) -> str:
        if self.is_fallback or not self.available:
            return "hash-fallback"
        return self.resolved_model or self.model

    def _active_dim(self) -> int:
        return int(self.embedding_dim or self.fallback_dim)

    def _make_cache_key(
        self,
        text: str,
        *,
        backend: str | None = None,
        model: str | None = None,
        dim: int | None = None,
        mode: str | None = None,
    ) -> str:
        """Hash full text + backend/model/dim/mode metadata (no truncation)."""
        text_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        meta = {
            "backend": backend if backend is not None else self._backend_label(),
            "model": model if model is not None else self._active_model(),
            "dim": int(dim if dim is not None else self._active_dim()),
            "mode": mode if mode is not None else self._mode_label(),
            "text_sha256": text_digest,
        }
        blob = json.dumps(meta, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def _cache_get(self, key: str) -> np.ndarray | None:
        vec = self._cache.get(key)
        if vec is None:
            return None
        self._cache.move_to_end(key)
        return vec

    def _cache_put(self, key: str, vec: np.ndarray) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = vec
        while len(self._cache) > _CACHE_MAX:
            self._cache.popitem(last=False)

    def _lookup_cached(self, text: str) -> np.ndarray | None:
        """Try expected ollama key first, then hash-fallback key."""
        candidates: list[tuple[str, str, str, int]] = []
        if self.use_ollama and self.available and not self.is_fallback:
            candidates.append(
                (
                    "ollama",
                    self.resolved_model or self.model,
                    "ollama",
                    self._active_dim(),
                )
            )
        candidates.append(
            ("hash", "hash-fallback", "hash_fallback", self.fallback_dim)
        )
        for backend, model, mode, dim in candidates:
            key = self._make_cache_key(
                text, backend=backend, model=model, dim=dim, mode=mode
            )
            hit = self._cache_get(key)
            if hit is not None:
                return hit
        return None

    def _fetch_tags(self) -> list[str]:
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/tags", headers={"Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
            return []

    def _resolve_model(self, names: list[str]) -> str:
        embed_names = [n for n in names if _is_embedding_model(n)]
        if not embed_names:
            return ""
        pin = _env_bool("CEREBRO_EMBED_PIN", False)
        if pin:
            # Exact model only — no silent substitution.
            if self.model in embed_names:
                return self.model
            self.last_error = (
                f"CEREBRO_EMBED_PIN=1: requested model {self.model!r} not found"
            )
            return ""
        if self.model in embed_names:
            return self.model
        base = self.model.split(":")[0]
        for n in embed_names:
            if n == base or n.startswith(base + ":"):
                return n
        for pref in (
            "nomic-embed-text",
            "mxbai-embed-large",
            "all-minilm",
            "snowflake-arctic-embed",
        ):
            for n in embed_names:
                if n.startswith(pref):
                    return n
        return embed_names[0]

    def ping(self) -> bool:
        names = self._fetch_tags()
        embed_names = [n for n in names if _is_embedding_model(n)]
        if not embed_names:
            self.available = False
            self.resolved_model = ""
            self.is_fallback = True
            return False
        self.resolved_model = self._resolve_model(embed_names)
        if not self.resolved_model:
            self.available = False
            self.is_fallback = True
            return False
        probe = self._embed_ollama("probe")
        if probe is None:
            self.available = False
            self.is_fallback = True
            return False
        self.embedding_dim = int(probe.size)
        self.available = True
        self.is_fallback = False
        return self.available

    def _embed_ollama(self, text: str) -> np.ndarray | None:
        if not text.strip():
            return None
        model = self.resolved_model or self.model
        payload = json.dumps({"model": model, "input": text[:2000]}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/embed",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            embs = body.get("embeddings")
            if embs and len(embs) > 0:
                vec = np.asarray(embs[0], dtype=np.float32)
                return _normalize(vec)
            emb = body.get("embedding")
            if emb:
                vec = np.asarray(emb, dtype=np.float32)
                return _normalize(vec)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
            self.last_error = str(e)
            self.available = False
            self.is_fallback = True
        return None

    def _embed_fallback(self, text: str) -> np.ndarray:
        self.is_fallback = True
        vec = encode_text(text, self.fallback_dim)
        if self.embedding_dim <= 0:
            self.embedding_dim = self.fallback_dim
        return _normalize(vec)

    def embed(self, text: str, *, use_cache: bool = True) -> np.ndarray:
        cleaned = text.strip()
        if not cleaned:
            self.is_fallback = True
            return np.zeros(self.fallback_dim, dtype=np.float32)
        if use_cache:
            hit = self._lookup_cached(cleaned)
            if hit is not None:
                return hit
        vec = None
        if self.use_ollama and (self.available or self.ping()):
            vec = self._embed_ollama(cleaned)
            if vec is not None:
                self.is_fallback = False
        if vec is None:
            vec = self._embed_fallback(cleaned)
        if use_cache:
            if self.is_fallback:
                key = self._make_cache_key(
                    cleaned,
                    backend="hash",
                    model="hash-fallback",
                    dim=self.fallback_dim,
                    mode="hash_fallback",
                )
            else:
                key = self._make_cache_key(
                    cleaned,
                    backend="ollama",
                    model=self.resolved_model or self.model,
                    dim=int(vec.size),
                    mode="ollama",
                )
            self._cache_put(key, vec)
        return vec

    def encode_blob(self, vec: np.ndarray) -> bytes:
        return np.asarray(vec, dtype=np.float32).tobytes()

    def decode_blob(self, blob: bytes | None) -> np.ndarray | None:
        if not blob:
            return None
        arr = np.frombuffer(blob, dtype=np.float32)
        if arr.size == 0:
            return None
        return arr.copy()

    @staticmethod
    def compatible(a: np.ndarray, b: np.ndarray) -> bool:
        return int(a.size) == int(b.size) and a.size > 0

    def similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        if not self.compatible(a, b):
            msg = (
                f"incompatible embedding dims: {int(a.size)} vs {int(b.size)}"
            )
            self.last_error = msg
            raise ValueError(msg)
        return _cosine(a, b)

    def memory_semantic_text(
        self,
        *,
        label: str,
        modality: str,
        room: str = "",
        tags: list[str] | None = None,
        body: dict | None = None,
    ) -> str:
        parts = [label, modality]
        if room:
            parts.append(f"habitación:{room}")
        if tags:
            parts.extend(tags[:4])
        if body:
            feel = body.get("feelings") or []
            if feel:
                parts.append(feel[0].get("signal", ""))
            drives = body.get("drives") or {}
            dom = max(drives.items(), key=lambda x: x[1], default=(None, 0))
            if dom[0] and dom[1] > 0.25:
                parts.append(str(dom[0]))
        return " | ".join(p for p in parts if p)

    def status(self) -> dict:
        fallback = bool(self.is_fallback or not (self.use_ollama and self.available))
        return {
            "backend": self._backend_label(),
            "model_requested": self.model,
            "model_used": self._active_model(),
            "model": self.resolved_model or self.model,
            "version": self._mode_label(),
            "mode": self._mode_label(),
            "dimension": self._active_dim(),
            "embedding_dim": self._active_dim(),
            "cache_size": len(self._cache),
            "last_error": self.last_error or None,
            "fallback": fallback,
            "is_fallback": fallback,
            "use_ollama": self.use_ollama,
            "available": self.available,
        }
