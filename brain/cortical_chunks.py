"""
Chunks corticales lazy — generación procedural por seed, cache en disco (estilo Minecraft).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from .engram_codec import decode_chunk_pattern, encode_chunk_pattern

if TYPE_CHECKING:
    from .connectome_blueprint import ConnectomeBlueprint


@dataclass
class CorticalChunk:
    region: str
    cx: int
    cy: int
    cz: int
    pattern: np.ndarray
    logical_neurons: int

    def chunk_id(self) -> str:
        return f"{self.region}_{self.cx}_{self.cy}_{self.cz}"


@dataclass
class CorticalChunkStore:
    blueprint: ConnectomeBlueprint
    cache_dir: Path
    chunk_neurons: int = 16384
    inject_gain: float = 0.08
    max_cached: int = 32
    _loaded: dict[str, CorticalChunk] = field(default_factory=dict, init=False)
    _cache_order: list[str] = field(default_factory=list, init=False)
    _session_loads: int = field(default=0, init=False)
    _session_prefetches: int = field(default=0, init=False)
    _session_bytes: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.cache_dir = Path(self.cache_dir)
        seed_dir = self.cache_dir / f"seed_{self.blueprint.seed}"
        self.chunks_dir = seed_dir / "chunks"
        self.chunks_dir.mkdir(parents=True, exist_ok=True)

    def _chunk_coords(self, region: str, focus: int) -> tuple[int, int, int]:
        h = hash((self.blueprint.seed, region, focus)) & 0xFFFFFF
        return (h & 0xF, (h >> 4) & 0xF, (h >> 8) & 0xF)

    def _generate(self, region: str, cx: int, cy: int, cz: int, dim: int) -> CorticalChunk:
        seed = hash((self.blueprint.seed, region, cx, cy, cz)) & 0x7FFFFFFF
        rng = np.random.default_rng(seed)
        pattern = rng.normal(0, 0.12, size=dim).astype(np.float32)
        _, weights = self.blueprint.sample_synapses(region, region, min(32, dim // 8), tick=cx + cy + cz)
        n = min(len(weights), pattern.size)
        pattern[:n] += weights[:n] * 0.25
        np.clip(pattern, -0.5, 0.5, out=pattern)
        return CorticalChunk(
            region=region,
            cx=cx,
            cy=cy,
            cz=cz,
            pattern=pattern,
            logical_neurons=self.chunk_neurons,
        )

    def _egck_path(self, region: str, cx: int, cy: int, cz: int) -> Path:
        return self.chunks_dir / region / f"{cx}_{cy}_{cz}.egck"

    def _legacy_npz_path(self, region: str, cx: int, cy: int, cz: int) -> Path:
        return self.chunks_dir / region / f"{cx}_{cy}_{cz}.npz"

    def _persist_chunk(self, chunk: CorticalChunk) -> None:
        path = self._egck_path(chunk.region, chunk.cx, chunk.cy, chunk.cz)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encode_chunk_pattern(chunk.pattern))
        legacy = self._legacy_npz_path(chunk.region, chunk.cx, chunk.cy, chunk.cz)
        if legacy.is_file():
            legacy.unlink(missing_ok=True)

    def _touch_cache(self, key: str) -> None:
        if key in self._cache_order:
            self._cache_order.remove(key)
        self._cache_order.append(key)
        while len(self._cache_order) > self.max_cached:
            evict = self._cache_order.pop(0)
            self._loaded.pop(evict, None)

    def _estimate_chunk_bytes(self, region: str, cx: int, cy: int, cz: int, dim: int) -> int:
        egck = self._egck_path(region, cx, cy, cz)
        if egck.is_file():
            return egck.stat().st_size
        legacy = self._legacy_npz_path(region, cx, cy, cz)
        if legacy.is_file():
            return legacy.stat().st_size
        return max(128, dim * 2)

    def load_chunk(
        self,
        region: str,
        cx: int,
        cy: int,
        cz: int,
        *,
        dim: int,
        governor=None,
    ) -> CorticalChunk:
        key = f"{region}:{cx}:{cy}:{cz}"
        if key in self._loaded:
            self._touch_cache(key)
            return self._loaded[key]

        egck = self._egck_path(region, cx, cy, cz)
        legacy = self._legacy_npz_path(region, cx, cy, cz)
        pattern: np.ndarray | None = None
        bytes_read = 0

        if egck.is_file():
            bytes_read = egck.stat().st_size
            if governor is not None and not governor.record(
                bytes_read, kind="chunk", label=f"{region}:{cx}_{cy}_{cz}"
            ):
                chunk = self._generate(region, cx, cy, cz, dim)
                self._loaded[key] = chunk
                return chunk
            pattern = decode_chunk_pattern(egck.read_bytes())
        elif legacy.is_file():
            bytes_read = legacy.stat().st_size
            if governor is not None and not governor.record(
                bytes_read, kind="chunk", label=f"legacy:{region}"
            ):
                chunk = self._generate(region, cx, cy, cz, dim)
                self._loaded[key] = chunk
                return chunk
            data = np.load(legacy)
            pattern = data["pattern"].astype(np.float32)
            logical = int(data.get("logical_neurons", self.chunk_neurons))
            data.close()
            chunk = CorticalChunk(
                region=region,
                cx=cx,
                cy=cy,
                cz=cz,
                pattern=pattern,
                logical_neurons=logical,
            )
            self._persist_chunk(chunk)
            self._loaded[key] = chunk
            self._session_loads += 1
            self._session_bytes += bytes_read
            self._touch_cache(key)
            return chunk

        if pattern is not None:
            chunk = CorticalChunk(
                region=region,
                cx=cx,
                cy=cy,
                cz=cz,
                pattern=pattern,
                logical_neurons=self.chunk_neurons,
            )
        else:
            chunk = self._generate(region, cx, cy, cz, dim)
            self._persist_chunk(chunk)

        self._loaded[key] = chunk
        self._session_loads += 1
        self._session_bytes += bytes_read
        self._touch_cache(key)
        return chunk

    def prefetch_for_focus(
        self,
        *,
        region: str,
        choice_key: str,
        dim: int,
        governor=None,
    ) -> bool:
        """Calienta chunk adyacente al foco sin consumir presupuesto principal."""
        base = self._chunk_coords(region, hash(choice_key) & 0xFFFF)
        cx, cy, cz = base[0] + 1, base[1], base[2]
        key = f"{region}:{cx}:{cy}:{cz}"
        if key in self._loaded:
            return False
        est = self._estimate_chunk_bytes(region, cx, cy, cz, dim)
        if governor is not None and not governor.record_prefetch(est, label=f"chunk:{region}"):
            return False
        self.load_chunk(region, cx, cy, cz, dim=dim, governor=None)
        self._session_prefetches += 1
        return True

    def load_for_focus(
        self,
        *,
        region: str,
        choice_key: str,
        dim: int,
        k: int = 2,
        governor=None,
    ) -> list[CorticalChunk]:
        max_k = max(1, k)
        if governor is not None:
            extra = 1 if governor.priority_boost > 0.4 else 0
            cap = governor.max_chunks + extra - governor.chunks_used
            max_k = max(0, min(k, cap))
            if max_k == 0:
                return []
        chunks: list[CorticalChunk] = []
        base = self._chunk_coords(region, hash(choice_key) & 0xFFFF)
        for i in range(max_k):
            cx, cy, cz = base[0] + i, base[1], base[2]
            chunks.append(
                self.load_chunk(region, cx, cy, cz, dim=dim, governor=governor)
            )
        return chunks

    def materialize_bias(self, chunks: list[CorticalChunk], dim: int) -> np.ndarray:
        if not chunks:
            return np.zeros(dim, dtype=np.float32)
        acc = np.zeros(dim, dtype=np.float32)
        for ch in chunks:
            p = ch.pattern
            if p.size >= dim:
                acc += p[:dim]
            else:
                acc[: p.size] += p
        acc /= max(len(chunks), 1)
        return (acc * self.inject_gain).astype(np.float32)

    def stats(self) -> dict:
        egck_count = sum(1 for _ in self.chunks_dir.rglob("*.egck"))
        legacy_count = sum(1 for _ in self.chunks_dir.rglob("*.npz"))
        egck_bytes = sum(f.stat().st_size for f in self.chunks_dir.rglob("*.egck"))
        return {
            "chunks_cached_session": len(self._loaded),
            "chunks_loaded_total": self._session_loads,
            "chunks_prefetched": self._session_prefetches,
            "bytes_decompressed": self._session_bytes,
            "egck_disk_bytes": egck_bytes,
            "codec": "EGCK",
            "egck_files": egck_count,
            "legacy_npz_files": legacy_count,
            "max_cached": self.max_cached,
            "cache_dir": str(self.chunks_dir),
        }
