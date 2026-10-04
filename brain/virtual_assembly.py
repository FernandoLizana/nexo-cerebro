"""
Ensambles celulares virtuales en disco (engramas corticales indexados).

Cada ensamble = grupo disperso de unidades lógicas en `.egm` (codec EGR1/EGRS);
SQLite indexa metadatos, firma LSH y vector-resumen para búsqueda por similitud.

Capacidad lógica: ensambles × neurons_per_assembly (p. ej. 4.4M × 20 ≈ 90M neuronas).
Solo los top-K ensambles recuperados se inyectan en el núcleo activo en RAM.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from .engram_codec import (
    decode_sparse,
    decode_summary,
    encode_sparse,
    encode_summary,
    estimate_sparse_bytes,
)

if TYPE_CHECKING:
    from .memory_store import EpisodicMemoryStore

BYTES_PER_ASSEMBLY_EST = 320


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na < 1e-6 or nb < 1e-6:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _sparse_from_pattern(
    pattern: np.ndarray,
    *,
    k: int,
    threshold: float = 0.08,
) -> tuple[np.ndarray, np.ndarray]:
    """Top-k unidades activas del patrón (codificación dispersa)."""
    p = np.asarray(pattern, dtype=np.float32).ravel()
    if p.size == 0:
        return np.zeros(0, dtype=np.int32), np.zeros(0, dtype=np.float32)
    idx = np.flatnonzero(p > threshold)
    if idx.size == 0:
        idx = np.array([int(np.argmax(p))], dtype=np.int32)
        w = np.array([float(p[idx[0]])], dtype=np.float32)
        return idx, w
    order = np.argsort(p[idx])[::-1][:k]
    sel = idx[order]
    return sel.astype(np.int32), p[sel].astype(np.float32)


@dataclass
class VirtualAssemblyStore:
    base_dir: Path
    pattern_dim: int = 384
    neurons_per_assembly: int = 20
    hot_size: int = 48
    disk_search_limit: int = 2500
    recall_k: int = 5
    inject_gain: float = 0.18
    disk_budget_gb: float = 12.0
    bytes_per_assembly: int = BYTES_PER_ASSEMBLY_EST
    lsh_bits: int = 16
    _hot: list[dict] = field(default_factory=list, init=False)
    _db: sqlite3.Connection | None = field(default=None, init=False)
    _lsh_proj: np.ndarray = field(default_factory=lambda: np.zeros(0), init=False)

    def __post_init__(self) -> None:
        self.base_dir = Path(self.base_dir)
        self.assemblies_dir = self.base_dir / "assemblies"
        self.assemblies_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.base_dir / "assembly_index.db"
        self._db = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS assemblies (
                key TEXT PRIMARY KEY,
                label TEXT,
                region TEXT,
                modality TEXT,
                strength REAL,
                valence REAL,
                arousal REAL,
                hits INTEGER,
                n_units INTEGER,
                summary BLOB,
                pattern_file TEXT,
                updated_at REAL
            )
            """
        )
        # LSH projection must exist before migrating signatures.
        self._init_lsh_projection()
        self._migrate_schema()
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_assemblies_updated ON assemblies(updated_at DESC)"
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_assemblies_lsh ON assemblies(lsh_sig)"
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_assemblies_strength ON assemblies(strength DESC)"
        )
        self._db.commit()
        self._load_hot_from_db()

    def _migrate_schema(self) -> None:
        cols = {r[1] for r in self._db.execute("PRAGMA table_info(assemblies)").fetchall()}
        if "lsh_sig" not in cols:
            self._db.execute("ALTER TABLE assemblies ADD COLUMN lsh_sig INTEGER DEFAULT 0")
        rows = self._db.execute(
            "SELECT key, summary FROM assemblies WHERE lsh_sig IS NULL OR lsh_sig = 0"
        ).fetchall()
        for row in rows:
            summary = self._decode_summary(row["summary"])
            if summary is None or np.asarray(summary).size == 0:
                continue
            try:
                sig = self._lsh_signature(summary)
            except ValueError:
                continue
            self._db.execute(
                "UPDATE assemblies SET lsh_sig = ? WHERE key = ?",
                (sig, row["key"]),
            )

    def _init_lsh_projection(self) -> None:
        path = self.base_dir / "lsh_projection.npy"
        bits = max(8, min(self.lsh_bits, 24))
        self.lsh_bits = bits
        dim = max(1, int(self.pattern_dim))
        self.pattern_dim = dim
        if path.exists():
            proj = np.load(path)
            if proj.shape == (bits, dim):
                self._lsh_proj = proj.astype(np.float32)
                return
        rng = np.random.default_rng(42)
        self._lsh_proj = rng.standard_normal((bits, dim)).astype(np.float32)
        np.save(path, self._lsh_proj)

    def _lsh_signature(self, vec: np.ndarray) -> int:
        if self._lsh_proj.size == 0:
            self._init_lsh_projection()
        v = np.asarray(vec, dtype=np.float32).ravel()
        if v.size == 0:
            return 0
        if v.size < self.pattern_dim:
            v = np.pad(v, (0, self.pattern_dim - v.size))
        v = v[: self.pattern_dim]
        bits = (self._lsh_proj @ v > 0).astype(np.uint8)
        sig = 0
        for i, b in enumerate(bits):
            if b:
                sig |= 1 << i
        return int(sig)

    def _lsh_neighbor_signatures(self, sig: int, *, radius: int = 1) -> list[int]:
        out = {sig}
        for i in range(self.lsh_bits):
            out.add(sig ^ (1 << i))
        if radius >= 2:
            base = list(out)
            for b in base:
                for i in range(self.lsh_bits):
                    for j in range(i + 1, self.lsh_bits):
                        out.add(b ^ (1 << i) ^ (1 << j))
        return list(out)

    @property
    def max_assemblies(self) -> int:
        budget = int(self.disk_budget_gb * (1024**3))
        return max(1000, budget // max(self.bytes_per_assembly, 500))

    @property
    def max_virtual_neurons(self) -> int:
        return self.max_assemblies * self.neurons_per_assembly

    @property
    def capacity_remaining(self) -> int:
        return max(0, self.max_assemblies - self.total_count())

    def _load_hot_from_db(self) -> None:
        rows = self._db.execute(
            "SELECT * FROM assemblies ORDER BY updated_at DESC LIMIT ?",
            (self.hot_size,),
        ).fetchall()
        self._hot.clear()
        for row in rows:
            entry = self._row_to_entry(row, load_sparse=False)
            if entry:
                entry["summary"] = self._decode_summary(row["summary"])
                self._hot.append(entry)

    def _encode_summary(self, vec: np.ndarray) -> bytes:
        v = np.asarray(vec, dtype=np.float32).ravel()[: self.pattern_dim]
        if v.size < self.pattern_dim:
            v = np.pad(v, (0, self.pattern_dim - v.size))
        return encode_summary(v, dim=self.pattern_dim)

    def _decode_summary(self, blob: bytes | None) -> np.ndarray | None:
        if not blob:
            return None
        return decode_summary(blob, dim=self.pattern_dim)

    def _assembly_path(self, key: str) -> Path:
        return self.assemblies_dir / f"{key}.egm"

    def _legacy_npz_path(self, key: str) -> Path:
        return self.assemblies_dir / f"{key}.npz"

    def _save_sparse(self, key: str, indices: np.ndarray, weights: np.ndarray) -> str:
        path = self._assembly_path(key)
        path.write_bytes(encode_sparse(indices, weights))
        legacy = self._legacy_npz_path(key)
        if legacy.exists():
            legacy.unlink(missing_ok=True)
        return path.name

    def _load_sparse(
        self,
        key: str,
        *,
        governor=None,
    ) -> tuple[np.ndarray, np.ndarray] | None:
        egm = self._assembly_path(key)
        if egm.is_file():
            data = egm.read_bytes()
            if governor is not None and not governor.record(
                len(data), kind="assembly", label=f"sparse:{key[:8]}"
            ):
                return None
            try:
                return decode_sparse(data)
            except ValueError:
                pass
        legacy = self._legacy_npz_path(key)
        if legacy.is_file():
            if governor is not None:
                cost = legacy.stat().st_size
                if not governor.record(cost, kind="assembly", label=f"legacy:{key[:8]}"):
                    return None
            data = np.load(legacy)
            idx = np.asarray(data["indices"], dtype=np.int32)
            w = np.asarray(data["weights"], dtype=np.float32)
            data.close()
            self._save_sparse(key, idx, w)
            return idx, w
        return None

    def _row_to_entry(self, row: sqlite3.Row, *, load_sparse: bool) -> dict | None:
        summary = self._decode_summary(row["summary"])
        if summary is None:
            return None
        entry = {
            "key": row["key"],
            "label": row["label"],
            "region": row["region"],
            "modality": row["modality"],
            "strength": float(row["strength"]),
            "valence": float(row["valence"]),
            "arousal": float(row["arousal"]),
            "hits": int(row["hits"]),
            "n_units": int(row["n_units"]),
            "summary": summary,
        }
        if load_sparse:
            sparse = self._load_sparse(row["key"])
            if sparse:
                entry["indices"], entry["weights"] = sparse
        return entry

    @property
    def hot_entries(self) -> list[dict]:
        return self._hot

    def total_count(self) -> int:
        row = self._db.execute("SELECT COUNT(*) AS c FROM assemblies").fetchone()
        return int(row["c"]) if row else 0

    def virtual_neuron_count(self) -> int:
        return self.total_count() * self.neurons_per_assembly

    def disk_usage_bytes(self) -> dict:
        db_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0
        egm_bytes = sum(f.stat().st_size for f in self.assemblies_dir.glob("*.egm"))
        npz_bytes = sum(f.stat().st_size for f in self.assemblies_dir.glob("*.npz"))
        patterns_bytes = egm_bytes + npz_bytes
        total = db_bytes + patterns_bytes
        n = max(self.total_count(), 1)
        budget = int(self.disk_budget_gb * (1024**3))
        legacy = sum(1 for _ in self.assemblies_dir.glob("*.npz"))
        return {
            "index_db_bytes": db_bytes,
            "patterns_bytes": patterns_bytes,
            "egm_bytes": egm_bytes,
            "legacy_npz_bytes": npz_bytes,
            "legacy_npz_count": legacy,
            "codec": "EGR1/EGRS",
            "total_bytes": total,
            "budget_bytes": budget,
            "budget_gb": self.disk_budget_gb,
            "used_pct": round(100.0 * total / max(budget, 1), 2),
            "per_assembly_bytes": round(total / n),
            "estimated_capacity_multiplier": round(BYTES_PER_ASSEMBLY_EST / max(total / n, 1), 1)
            if total > n
            else 8.0,
            "assemblies": self.total_count(),
            "max_assemblies": self.max_assemblies,
            "capacity_remaining": self.capacity_remaining,
        }

    def estimate_capacity(
        self,
        *,
        target_virtual_neurons: int | None = None,
        assemblies: int | None = None,
    ) -> dict:
        """Estimación de disco para planificar escala."""
        if assemblies is None:
            if target_virtual_neurons is not None:
                assemblies = max(1, target_virtual_neurons // self.neurons_per_assembly)
            else:
                assemblies = self.max_assemblies
        per = self.disk_usage_bytes()["per_assembly_bytes"] if self.total_count() else self.bytes_per_assembly
        total_mb = (per * assemblies) / (1024 * 1024)
        return {
            "assemblies": assemblies,
            "neurons_per_assembly": self.neurons_per_assembly,
            "virtual_neurons": assemblies * self.neurons_per_assembly,
            "estimated_disk_mb": round(total_mb, 1),
            "estimated_disk_gb": round(total_mb / 1024, 3),
        }

    def _promote_hot(self, entry: dict) -> None:
        key = entry["key"]
        self._hot = [m for m in self._hot if m["key"] != key]
        self._hot.insert(0, entry)
        if len(self._hot) > self.hot_size:
            self._hot.pop()

    def _candidate_keys_from_lsh(self, sig: int) -> list[str]:
        keys: list[str] = []
        seen: set[str] = set()
        per_bucket = max(80, self.disk_search_limit // max(len(self._lsh_neighbor_signatures(sig)), 1))
        for nsig in self._lsh_neighbor_signatures(sig, radius=1):
            rows = self._db.execute(
                """
                SELECT key FROM assemblies
                WHERE lsh_sig = ?
                ORDER BY strength DESC, hits DESC
                LIMIT ?
                """,
                (nsig, per_bucket),
            ).fetchall()
            for row in rows:
                k = row["key"]
                if k not in seen:
                    seen.add(k)
                    keys.append(k)
                if len(keys) >= self.disk_search_limit:
                    return keys
        if len(keys) < self.recall_k * 4:
            rows = self._db.execute(
                """
                SELECT key FROM assemblies
                ORDER BY strength DESC, updated_at DESC
                LIMIT ?
                """,
                (self.disk_search_limit,),
            ).fetchall()
            for row in rows:
                k = row["key"]
                if k not in seen:
                    seen.add(k)
                    keys.append(k)
        return keys

    def recall_top_k(
        self,
        pattern: np.ndarray,
        *,
        k: int | None = None,
        threshold: float = 0.52,
        governor=None,
    ) -> list[dict]:
        k = k or self.recall_k
        if governor is not None:
            k = max(0, min(k, governor.effective_assembly_limit(k)))
            if k == 0:
                return []
        p = np.asarray(pattern, dtype=np.float32).ravel()
        if p.size < self.pattern_dim:
            p = np.pad(p, (0, self.pattern_dim - p.size))
        p = p[: self.pattern_dim]

        scored: list[tuple[float, dict]] = []
        hot_keys: set[str] = set()

        for mem in self._hot:
            hot_keys.add(mem["key"])
            s = _cosine(p, mem["summary"])
            if s >= threshold:
                scored.append((s, {**mem, "similarity": s}))

        sig = self._lsh_signature(p)
        for key in self._candidate_keys_from_lsh(sig):
            if key in hot_keys:
                continue
            meta = self._db.execute(
                "SELECT * FROM assemblies WHERE key = ?", (key,)
            ).fetchone()
            if not meta:
                continue
            blob = meta["summary"]
            if governor is not None and not governor.record(
                len(blob) if blob else 64,
                kind="assembly",
                label=str(meta["label"] or key)[:32],
            ):
                continue
            summary = self._decode_summary(blob)
            if summary is None:
                continue
            s = _cosine(p, summary)
            if s >= threshold:
                entry = self._row_to_entry(meta, load_sparse=False)
                if entry:
                    scored.append((s, {**entry, "similarity": s}))

        scored.sort(key=lambda x: x[0], reverse=True)
        out: list[dict] = []
        seen: set[str] = set()
        for s, entry in scored:
            if entry["key"] in seen:
                continue
            seen.add(entry["key"])
            entry["hits"] = entry.get("hits", 0) + 1
            self._db.execute(
                "UPDATE assemblies SET hits = ? WHERE key = ?",
                (entry["hits"], entry["key"]),
            )
            out.append(entry)
            if len(out) >= k:
                break
        if out:
            self._db.commit()
            self._promote_hot(out[0])
        return out

    def prefetch_for_pattern(
        self,
        pattern: np.ndarray,
        *,
        k: int = 2,
        governor=None,
    ) -> int:
        """Precarga ensambles LSH similares en hot cache (presupuesto prefetch)."""
        p = np.asarray(pattern, dtype=np.float32).ravel()
        if p.size < self.pattern_dim:
            p = np.pad(p, (0, self.pattern_dim - p.size))
        p = p[: self.pattern_dim]
        sig = self._lsh_signature(p)
        hot_keys = {m["key"] for m in self._hot}
        warmed = 0
        for key in self._candidate_keys_from_lsh(sig):
            if key in hot_keys:
                continue
            meta = self._db.execute(
                "SELECT * FROM assemblies WHERE key = ?", (key,)
            ).fetchone()
            if not meta:
                continue
            blob = meta["summary"]
            cost = len(blob) if blob else 64
            if governor is not None and not governor.record_prefetch(
                cost, label=str(meta["label"] or key)[:32]
            ):
                break
            entry = self._row_to_entry(meta, load_sparse=False)
            if entry:
                self._promote_hot(entry)
                hot_keys.add(entry["key"])
                warmed += 1
            if warmed >= k:
                break
        return warmed

    def _summary_from_sparse(
        self,
        indices: np.ndarray,
        weights: np.ndarray,
        pattern: np.ndarray,
    ) -> np.ndarray:
        summary = np.asarray(pattern, dtype=np.float32).ravel()[: self.pattern_dim].copy()
        if summary.size < self.pattern_dim:
            summary = np.pad(summary, (0, self.pattern_dim - summary.size))
        for i, w in zip(indices, weights):
            if 0 <= i < self.pattern_dim:
                summary[i] = max(summary[i], float(w))
        m = float(summary.max())
        if m > 1e-6:
            summary /= m
        return np.clip(summary, 0.0, 1.0)

    def ingest(
        self,
        pattern: np.ndarray,
        *,
        label: str,
        modality: str = "world",
        region: str = "associative",
        valence: float = 0.0,
        arousal: float = 0.0,
        strength: float = 1.0,
        force: bool = False,
    ) -> dict | None:
        """Consolidar patrón en un ensamble virtual (sueño / replay)."""
        if not force and self.total_count() >= self.max_assemblies:
            return None

        import hashlib

        p = np.asarray(pattern, dtype=np.float32).ravel()
        if p.size < self.pattern_dim:
            p = np.pad(p, (0, self.pattern_dim - p.size))
        p = p[: self.pattern_dim]
        indices, weights = _sparse_from_pattern(p, k=self.neurons_per_assembly)
        key = hashlib.sha1(
            indices.tobytes() + label.encode("utf-8") + p.tobytes()
        ).hexdigest()[:14]
        now = time.time()
        summary = self._summary_from_sparse(indices, weights, p)
        lsh_sig = self._lsh_signature(summary)
        existing = self._db.execute(
            "SELECT * FROM assemblies WHERE key = ?", (key,)
        ).fetchone()

        if existing:
            new_strength = min(
                1.0,
                0.85 * float(existing["strength"]) + 0.15 * strength,
            )
            valence = 0.7 * float(existing["valence"]) + 0.3 * valence
            arousal = 0.7 * float(existing["arousal"]) + 0.3 * arousal
            self._save_sparse(key, indices, weights)
            self._db.execute(
                """
                UPDATE assemblies SET label=?, region=?, modality=?, strength=?,
                valence=?, arousal=?, n_units=?, lsh_sig=?, summary=?, updated_at=? WHERE key=?
                """,
                (
                    label,
                    region,
                    modality,
                    new_strength,
                    valence,
                    arousal,
                    int(indices.size),
                    lsh_sig,
                    self._encode_summary(summary),
                    now,
                    key,
                ),
            )
            hits = int(existing["hits"])
        else:
            new_strength = float(np.clip(strength, 0.05, 1.0))
            pf = self._save_sparse(key, indices, weights)
            self._db.execute(
                """
                INSERT INTO assemblies (key, label, region, modality, strength,
                valence, arousal, hits, n_units, lsh_sig, summary, pattern_file, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)
                """,
                (
                    key,
                    label,
                    region,
                    modality,
                    new_strength,
                    valence,
                    arousal,
                    int(indices.size),
                    lsh_sig,
                    self._encode_summary(summary),
                    pf,
                    now,
                ),
            )
            hits = 0

        self._db.commit()
        entry = {
            "key": key,
            "label": label,
            "region": region,
            "modality": modality,
            "strength": new_strength,
            "valence": valence,
            "arousal": arousal,
            "hits": hits,
            "n_units": int(indices.size),
            "summary": summary,
            "indices": indices,
            "weights": weights,
        }
        self._promote_hot(entry)
        return entry

    def inject(
        self,
        sensory: np.ndarray,
        *,
        k: int | None = None,
        threshold: float = 0.52,
        governor=None,
    ) -> tuple[np.ndarray, dict]:
        """Recupera ensambles similares e inyecta señal débil en el patrón sensorial."""
        base = np.asarray(sensory, dtype=np.float32).ravel().copy()
        if base.size < self.pattern_dim:
            base = np.pad(base, (0, self.pattern_dim - base.size))
        base = base[: self.pattern_dim]

        recalled = self.recall_top_k(base, k=k, threshold=threshold, governor=governor)
        if not recalled:
            meta = {"recalled": 0, "assemblies": [], "inject_energy": 0.0}
            if governor is not None and governor.blocked:
                meta["governor_blocked"] = True
            return base, meta

        boost = np.zeros(self.pattern_dim, dtype=np.float32)
        labels: list[str] = []
        for asm in recalled:
            sim = float(asm.get("similarity", 0.5))
            w = self.inject_gain * asm["strength"] * sim
            boost += w * asm["summary"]
            labels.append(asm.get("label", "?")[:32])

        merged = np.clip(base + boost, 0.0, 1.0)
        m = float(merged.max())
        if m > 1e-6:
            merged /= m
        energy = float(np.linalg.norm(boost))
        return merged, {
            "recalled": len(recalled),
            "assemblies": labels,
            "inject_energy": round(energy, 4),
            "similarities": [round(a.get("similarity", 0), 3) for a in recalled],
            "governor_bytes": governor.bytes_used if governor else None,
        }

    def inject_to_lobes(
        self,
        sensory: np.ndarray,
        *,
        n_per_lobe: int,
        k: int | None = None,
        threshold: float = 0.52,
        governor=None,
    ) -> tuple[dict[str, np.ndarray], dict]:
        """
        Recupera ensambles e inyecta en columnas por lóbulo (no solo sensory 384-D).
        Occipital/temporal/parietal/frontal reciben bandas del summary.
        """
        base = np.asarray(sensory, dtype=np.float32).ravel()
        recalled = self.recall_top_k(base, k=k, threshold=threshold, governor=governor)
        n = max(8, int(n_per_lobe))
        empty = {name: np.zeros(n, dtype=np.float32) for name in ("occipital", "temporal", "parietal", "frontal")}
        if not recalled:
            return empty, {"recalled": 0, "lobes": False}

        acc = {name: np.zeros(n, dtype=np.float32) for name in empty}
        labels: list[str] = []
        for asm in recalled:
            sim = float(asm.get("similarity", 0.5))
            w = self.inject_gain * float(asm.get("strength", 0.5)) * sim
            summary = np.asarray(asm["summary"], dtype=np.float32).ravel()
            # 4 bandas del summary → 4 lóbulos
            bands = np.array_split(summary, 4) if summary.size >= 4 else [summary] * 4
            for name, band in zip(("occipital", "temporal", "parietal", "frontal"), bands):
                b = band.ravel()
                if b.size < n:
                    b = np.pad(b, (0, n - b.size))
                acc[name] += w * b[:n]
            labels.append(asm.get("label", "?")[:32])

        for name in acc:
            m = float(np.max(np.abs(acc[name])))
            if m > 1e-6:
                acc[name] = np.clip(acc[name] / m, 0, 1)
        return acc, {"recalled": len(recalled), "assemblies": labels, "lobes": True}

    def sleep_consolidate(
        self,
        *,
        merge_threshold: float = 0.91,
        prune_strength: float = 0.04,
        max_merges: int = 120,
        scan_limit: int = 4000,
    ) -> dict:
        """Fusión de ensambles redundantes y poda de débiles (NREM lento)."""
        merged = 0
        pruned = 0
        rows = self._db.execute(
            """
            SELECT key, summary, strength FROM assemblies
            ORDER BY strength DESC, updated_at DESC
            LIMIT ?
            """,
            (scan_limit,),
        ).fetchall()
        summaries: list[np.ndarray] = []
        keys: list[str] = []
        for row in rows:
            s = self._decode_summary(row["summary"])
            if s is not None:
                summaries.append(s)
                keys.append(row["key"])

        drop: set[str] = set()
        for i in range(len(keys)):
            if keys[i] in drop or merged >= max_merges:
                continue
            for j in range(i + 1, min(i + 80, len(keys))):
                if keys[j] in drop:
                    continue
                if _cosine(summaries[i], summaries[j]) >= merge_threshold:
                    self._db.execute(
                        """
                        UPDATE assemblies SET strength = MIN(1.0, strength + 0.08)
                        WHERE key = ?
                        """,
                        (keys[i],),
                    )
                    drop.add(keys[j])
                    merged += 1
                    if merged >= max_merges:
                        break

        for key in drop:
            self._db.execute("DELETE FROM assemblies WHERE key = ?", (key,))
            self._assembly_path(key).unlink(missing_ok=True)
            pruned += 1

        weak = self._db.execute(
            "SELECT key FROM assemblies WHERE strength < ? LIMIT 500",
            (prune_strength,),
        ).fetchall()
        for row in weak:
            key = row["key"]
            if key in drop:
                continue
            self._db.execute("DELETE FROM assemblies WHERE key = ?", (key,))
            self._assembly_path(key).unlink(missing_ok=True)
            pruned += 1

        self._db.commit()
        self._load_hot_from_db()
        return {
            "merged": merged,
            "pruned": pruned,
            "remaining": self.total_count(),
            "capacity_pct": round(100.0 * self.total_count() / max(self.max_assemblies, 1), 3),
        }

    def bootstrap_from_memories(
        self,
        memory_store: EpisodicMemoryStore,
        *,
        limit: int | None = None,
    ) -> dict:
        """Importa recuerdos episódicos existentes como ensambles virtuales."""
        rows = memory_store._db.execute(
            "SELECT key, label, modality, valence, arousal FROM memories ORDER BY updated_at DESC"
        ).fetchall()
        ingested = 0
        skipped = 0
        cap = limit if limit is not None else self.capacity_remaining
        for row in rows:
            if ingested >= cap:
                break
            pat = memory_store._load_pattern_bundle(row["key"])
            if pat is None:
                skipped += 1
                continue
            pattern = pat.get("pattern", pat.get("sensory"))
            if pattern is None:
                skipped += 1
                continue
            result = self.ingest(
                pattern,
                label=row["label"] or "memoria",
                modality=row["modality"] or "text",
                valence=float(row["valence"]),
                arousal=float(row["arousal"]),
                strength=0.72,
            )
            if result:
                ingested += 1
            else:
                skipped += 1
                break
        return {
            "ingested": ingested,
            "skipped": skipped,
            "total_assemblies": self.total_count(),
            "virtual_neurons": self.virtual_neuron_count(),
            "capacity_remaining": self.capacity_remaining,
        }

    def list_recent(self, n: int = 6) -> list[dict]:
        rows = self._db.execute(
            """
            SELECT label, region, strength, n_units, valence
            FROM assemblies ORDER BY updated_at DESC LIMIT ?
            """,
            (n,),
        ).fetchall()
        return [
            {
                "label": r["label"],
                "region": r["region"],
                "strength": round(float(r["strength"]), 3),
                "units": r["n_units"],
                "valence": round(float(r["valence"]), 3),
            }
            for r in rows
        ]

    def clear(self) -> None:
        self._hot.clear()
        self._db.execute("DELETE FROM assemblies")
        self._db.commit()
        for f in self.assemblies_dir.glob("*.npz"):
            f.unlink(missing_ok=True)

    def close(self) -> None:
        if self._db:
            self._db.close()
            self._db = None
