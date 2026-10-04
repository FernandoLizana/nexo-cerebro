"""
Memoria episódica en disco: patrones multimodales en .npz, índice en SQLite.

Cada recuerdo incluye percepción + contexto (cuerpo, habitación, acción).
Solo un subconjunto «caliente» permanece en RAM; el resto se carga bajo demanda.
"""

from __future__ import annotations

import json
import math
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from .episodic_context import (
    CONTEXT_DIM,
    build_context_vector,
    fuse_episodic_pattern,
    multimodal_similarity,
)

if TYPE_CHECKING:
    from .embeddings import SemanticEmbedder

SEMANTIC_RECALL_WEIGHT = 0.55
PATTERN_RECALL_WEIGHT = 0.45


@dataclass
class EpisodicMemoryStore:
    base_dir: Path
    hot_size: int = 16
    disk_search_limit: int = 400
    pattern_dim: int = 384
    recall_threshold: float = 0.62
    _hot: list[dict] = field(default_factory=list, init=False)
    _db: sqlite3.Connection | None = field(default=None, init=False)
    _embedder: SemanticEmbedder | None = field(default=None, init=False)

    def attach_embedder(self, embedder: SemanticEmbedder) -> None:
        self._embedder = embedder

    def __post_init__(self) -> None:
        self.base_dir = Path(self.base_dir)
        self.patterns_dir = self.base_dir / "memories"
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.base_dir / "memory_index.db"
        self._db = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                key TEXT PRIMARY KEY,
                label TEXT,
                modality TEXT,
                valence REAL,
                arousal REAL,
                count INTEGER,
                hits INTEGER,
                tags TEXT,
                motor TEXT,
                room TEXT,
                pattern_file TEXT,
                updated_at REAL
            )
            """
        )
        self._migrate_schema()
        self._db.commit()
        self._load_hot_from_db()

    def _migrate_schema(self) -> None:
        cols = {r[1] for r in self._db.execute("PRAGMA table_info(memories)").fetchall()}
        if "room" not in cols:
            self._db.execute("ALTER TABLE memories ADD COLUMN room TEXT DEFAULT ''")
        if "embedding" not in cols:
            self._db.execute("ALTER TABLE memories ADD COLUMN embedding BLOB")

    def _load_hot_from_db(self) -> None:
        rows = self._db.execute(
            "SELECT * FROM memories ORDER BY updated_at DESC LIMIT ?", (self.hot_size,)
        ).fetchall()
        self._hot.clear()
        for row in rows:
            entry = self._row_to_entry(row, load_pattern=True)
            if entry:
                self._hot.append(entry)

    def _pattern_path(self, key: str) -> Path:
        return self.patterns_dir / f"{key}.npz"

    def _save_pattern_bundle(
        self,
        key: str,
        *,
        sensory: np.ndarray,
        context: np.ndarray,
        fused: np.ndarray,
    ) -> str:
        path = self._pattern_path(key)
        np.savez_compressed(
            path,
            sensory=np.asarray(sensory, dtype=np.float32),
            context=np.asarray(context, dtype=np.float32),
            pattern=np.asarray(fused, dtype=np.float32),
        )
        return str(path.name)

    def _load_pattern_bundle(self, key: str) -> dict[str, np.ndarray] | None:
        path = self._pattern_path(key)
        if not path.exists():
            return None
        data = np.load(path)
        if "sensory" in data:
            return {
                "sensory": np.asarray(data["sensory"], dtype=np.float32),
                "context": np.asarray(data["context"], dtype=np.float32),
                "pattern": np.asarray(data["pattern"], dtype=np.float32),
            }
        # Legacy: solo pattern
        pat = np.asarray(data["pattern"], dtype=np.float32)
        return {
            "sensory": pat.copy(),
            "context": np.zeros(CONTEXT_DIM, dtype=np.float32),
            "pattern": pat,
        }

    def _row_to_entry(self, row: sqlite3.Row, *, load_pattern: bool) -> dict | None:
        bundle = self._load_pattern_bundle(row["key"]) if load_pattern else None
        if load_pattern and bundle is None:
            return None
        entry = {
            "key": row["key"],
            "label": row["label"],
            "modality": row["modality"],
            "valence": float(row["valence"]),
            "arousal": float(row["arousal"]),
            "count": int(row["count"]),
            "hits": int(row["hits"]),
            "tags": json.loads(row["tags"] or "[]"),
            "motor": json.loads(row["motor"] or "[]"),
            "room": row["room"] or "",
        }
        if bundle is not None:
            entry["sensory"] = bundle["sensory"]
            entry["context"] = bundle["context"]
            entry["pattern"] = bundle["pattern"]
        if "embedding" in row.keys() and row["embedding"]:
            entry["embedding"] = self._decode_embedding(row["embedding"])
        return entry

    def _decode_embedding(self, blob: bytes | None) -> np.ndarray | None:
        if self._embedder:
            return self._embedder.decode_blob(blob)
        if not blob:
            return None
        return np.frombuffer(blob, dtype=np.float32).copy()

    def _memory_embedding(self, mem: dict, row: sqlite3.Row | None = None) -> np.ndarray | None:
        expected = (
            self._embedder.embedding_dim
            if self._embedder and self._embedder.available
            else (self._embedder.fallback_dim if self._embedder else 0)
        )
        if mem.get("embedding") is not None:
            emb = mem["embedding"]
            if expected and emb.size != expected:
                mem.pop("embedding", None)
            else:
                return emb
        if row is not None and "embedding" in row.keys() and row["embedding"]:
            emb = self._decode_embedding(row["embedding"])
            if emb is not None:
                if expected and emb.size != expected:
                    emb = None
                else:
                    mem["embedding"] = emb
                    return emb
        if not self._embedder:
            return None
        text = self._embedder.memory_semantic_text(
            label=mem.get("label", ""),
            modality=mem.get("modality", "world"),
            room=mem.get("room", ""),
            tags=mem.get("tags"),
        )
        emb = self._embedder.embed(text)
        mem["embedding"] = emb
        return emb

    @property
    def hot_entries(self) -> list[dict]:
        return self._hot

    def total_count(self) -> int:
        row = self._db.execute("SELECT COUNT(*) AS c FROM memories").fetchone()
        return int(row["c"]) if row else 0

    def _score_recall(
        self,
        query_sensory: np.ndarray,
        query_ctx: np.ndarray,
        query_room: str,
        mem: dict,
        *,
        query_embed: np.ndarray | None = None,
        row: sqlite3.Row | None = None,
    ) -> float:
        pattern_score = multimodal_similarity(
            query_sensory,
            query_ctx,
            query_room,
            mem.get("sensory", mem.get("pattern")),
            mem.get("context", np.zeros(CONTEXT_DIM, dtype=np.float32)),
            mem.get("room", ""),
        )
        if query_embed is None or not self._embedder or not self._embedder.available:
            return pattern_score
        mem_embed = self._memory_embedding(mem, row=row)
        if mem_embed is None:
            return pattern_score
        if not self._embedder.compatible(query_embed, mem_embed):
            return pattern_score
        sem = self._embedder.similarity(query_embed, mem_embed)
        return PATTERN_RECALL_WEIGHT * pattern_score + SEMANTIC_RECALL_WEIGHT * sem

    def semantic_search(self, text: str, *, k: int = 5, threshold: float = 0.55) -> list[dict]:
        """Búsqueda semántica para memoria de trabajo."""
        if not self._embedder or not self._embedder.available or not text.strip():
            return []
        query = self._embedder.embed(text.strip())
        scored: list[tuple[float, dict]] = []
        rows = self._db.execute(
            "SELECT * FROM memories ORDER BY updated_at DESC LIMIT ?",
            (self.disk_search_limit,),
        ).fetchall()
        for row in rows:
            mem = self._row_to_entry(row, load_pattern=False)
            if not mem:
                continue
            emb = self._memory_embedding(mem, row=row)
            if emb is None or not self._embedder.compatible(query, emb):
                continue
            s = self._embedder.similarity(query, emb)
            if s >= threshold:
                scored.append((s, {**mem, "similarity": s}))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:k]]

    def search_language_tutor(
        self,
        text: str,
        *,
        k: int = 3,
        threshold: float = 0.50,
    ) -> list[dict]:
        """RAG: frases aprendidas del tutor semejantes al mensaje del cuidador."""
        query = (text or "").strip()
        scored: list[tuple[float, dict]] = []
        rows = self._db.execute(
            "SELECT * FROM memories WHERE modality = ? ORDER BY updated_at DESC LIMIT ?",
            ("language_tutor", self.disk_search_limit),
        ).fetchall()
        if not query:
            for row in rows[:k]:
                mem = self._row_to_entry(row, load_pattern=False)
                if mem:
                    scored.append((0.5, {**mem, "similarity": 0.5}))
            return [m for _, m in scored[:k]]
        if self._embedder and self._embedder.available:
            q_emb = self._embedder.embed(query)
            for row in rows:
                mem = self._row_to_entry(row, load_pattern=False)
                if not mem:
                    continue
                emb = self._memory_embedding(mem, row=row)
                if emb is None or not self._embedder.compatible(q_emb, emb):
                    continue
                s = self._embedder.similarity(q_emb, emb)
                if s >= threshold:
                    scored.append((s, {**mem, "similarity": s}))
        else:
            q_low = query.lower()
            for row in rows:
                mem = self._row_to_entry(row, load_pattern=False)
                if not mem:
                    continue
                label = (mem.get("label") or "").lower()
                score = 0.35
                if q_low and q_low[:24] in label:
                    score = 0.85
                elif q_low and any(w in label for w in q_low.split() if len(w) >= 4):
                    score = 0.62
                scored.append((score, {**mem, "similarity": score}))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:k]]

    def count_by_modality(self, modality: str) -> int:
        row = self._db.execute(
            "SELECT COUNT(*) AS n FROM memories WHERE modality = ?",
            (modality,),
        ).fetchone()
        return int(row["n"]) if row else 0

    def search_by_tags(self, tags: list[str], *, k: int = 5) -> list[dict]:
        """Fallback cuando no hay embeddings: solapamiento de tags."""
        if not tags:
            return []
        want = {t.lower() for t in tags}
        scored: list[tuple[float, dict]] = []
        rows = self._db.execute(
            "SELECT * FROM memories ORDER BY updated_at DESC LIMIT ?",
            (self.disk_search_limit,),
        ).fetchall()
        for row in rows:
            mem = self._row_to_entry(row, load_pattern=False)
            if not mem:
                continue
            mem_tags = {str(t).lower() for t in (mem.get("tags") or [])}
            overlap = len(want & mem_tags)
            if overlap == 0:
                label = (mem.get("label") or "").lower()
                if any(t in label for t in want):
                    overlap = 1
            if overlap > 0:
                scored.append((overlap + mem.get("count", 1) * 0.01, mem))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:k]]

    def recall_for_symbol(self, arc_tags: list[str], query_text: str, *, k: int = 3) -> list[dict]:
        hits = self.semantic_search(query_text, k=k, threshold=0.42)
        if hits:
            return hits
        return self.search_by_tags(arc_tags, k=k)

    def recall(
        self,
        pattern: np.ndarray,
        *,
        body: dict[str, Any] | None = None,
        room: str = "",
        motor: list[int] | None = None,
        semantic_text: str | None = None,
        threshold: float | None = None,
        brain=None,
    ) -> dict | None:
        threshold = self.recall_threshold if threshold is None else threshold
        dynamics = getattr(brain, "memory_dynamics", None) if brain else None
        flags = getattr(brain, "experiment_flags", None) if brain else None
        use_dynamics = bool(
            dynamics
            and flags
            and getattr(flags, "enable_memory_dynamics", False)
        )
        query_sensory = np.asarray(pattern, dtype=np.float32)
        if body is not None:
            query_ctx = build_context_vector(body=body, room=room, motor=motor or [])
        else:
            _, query_ctx = fuse_episodic_pattern(
                query_sensory,
                n=self.pattern_dim,
                body={},
                room=room,
                motor=motor or [],
            )

        query_embed = None
        if self._embedder and self._embedder.available and semantic_text:
            query_embed = self._embedder.embed(semantic_text)

        best, score = None, -1.0
        for mem in self._hot:
            s = self._score_recall(
                query_sensory, query_ctx, room, mem, query_embed=query_embed
            )
            if use_dynamics:
                s = dynamics.adjust_recall_score(brain, mem, s)
            if s > score:
                score, best = s, mem
        if best and score > threshold:
            best["hits"] = best.get("hits", 0) + 1
            self._db.execute(
                "UPDATE memories SET hits = ? WHERE key = ?",
                (best["hits"], best["key"]),
            )
            self._db.commit()
            result = {**best, "similarity": score, "semantic": query_embed is not None}
            if use_dynamics:
                result = dynamics.post_recall(brain, result)
            return result

        rows = self._db.execute(
            "SELECT * FROM memories ORDER BY updated_at DESC LIMIT ?",
            (self.disk_search_limit,),
        ).fetchall()
        hot_keys = {m["key"] for m in self._hot}
        for row in rows:
            key = row["key"]
            if key in hot_keys:
                continue
            mem = self._row_to_entry(row, load_pattern=True)
            if not mem:
                continue
            s = self._score_recall(
                query_sensory,
                query_ctx,
                room,
                mem,
                query_embed=query_embed,
                row=row,
            )
            if use_dynamics:
                s = dynamics.adjust_recall_score(brain, mem, s)
            if s > score:
                score, best = s, mem

        if best and score > threshold:
            best["hits"] = best.get("hits", 0) + 1
            self._db.execute(
                "UPDATE memories SET hits = ? WHERE key = ?",
                (best["hits"], best["key"]),
            )
            self._db.commit()
            self._promote_hot(best)
            result = {**best, "similarity": score, "semantic": query_embed is not None}
            if use_dynamics:
                result = dynamics.post_recall(brain, result)
            return result
        return None

    def _promote_hot(self, entry: dict) -> None:
        key = entry["key"]
        self._hot = [m for m in self._hot if m["key"] != key]
        self._hot.insert(0, entry)
        if len(self._hot) > self.hot_size:
            self._hot.pop()

    def store(
        self,
        key: str,
        pattern: np.ndarray,
        *,
        label: str,
        modality: str,
        motor: list[int],
        valence: float,
        arousal: float,
        tags: list[str] | None = None,
        body: dict[str, Any] | None = None,
        room: str = "",
        olfaction: dict | None = None,
        affect: dict | None = None,
        posture: dict | None = None,
    ) -> dict:
        now = time.time()
        existing = self._db.execute(
            "SELECT * FROM memories WHERE key = ?", (key,)
        ).fetchone()
        sensory = np.asarray(pattern, dtype=np.float32).copy()
        fused, ctx = fuse_episodic_pattern(
            sensory,
            n=self.pattern_dim,
            body=body or {},
            room=room,
            motor=motor,
            olfaction=olfaction,
            affect=affect,
            posture=posture,
        )
        tag_json = json.dumps(tags or [], ensure_ascii=False)
        motor_json = json.dumps(motor)

        embed_blob = None
        if self._embedder:
            sem_text = self._embedder.memory_semantic_text(
                label=label,
                modality=modality,
                room=room,
                tags=tags,
                body=body,
            )
            embed_blob = self._embedder.encode_blob(self._embedder.embed(sem_text))

        if existing:
            count = int(existing["count"]) + 1
            valence = 0.7 * float(existing["valence"]) + 0.3 * valence
            arousal = 0.7 * float(existing["arousal"]) + 0.3 * arousal
            old_tags = json.loads(existing["tags"] or "[]")
            merged_tags = list(set(old_tags + (tags or [])))
            tag_json = json.dumps(merged_tags, ensure_ascii=False)
            self._save_pattern_bundle(key, sensory=sensory, context=ctx, fused=fused)
            if embed_blob is not None:
                self._db.execute(
                    """
                    UPDATE memories SET label=?, modality=?, valence=?, arousal=?,
                    count=?, motor=?, tags=?, room=?, embedding=?, updated_at=? WHERE key=?
                    """,
                    (
                        label, modality, valence, arousal, count, motor_json,
                        tag_json, room, embed_blob, now, key,
                    ),
                )
            else:
                self._db.execute(
                    """
                    UPDATE memories SET label=?, modality=?, valence=?, arousal=?,
                    count=?, motor=?, tags=?, room=?, updated_at=? WHERE key=?
                    """,
                    (label, modality, valence, arousal, count, motor_json, tag_json, room, now, key),
                )
        else:
            count = 1
            self._save_pattern_bundle(key, sensory=sensory, context=ctx, fused=fused)
            self._db.execute(
                """
                INSERT INTO memories (key, label, modality, valence, arousal,
                count, hits, tags, motor, room, embedding, pattern_file, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?)
                """,
                (
                    key,
                    label,
                    modality,
                    valence,
                    arousal,
                    count,
                    tag_json,
                    motor_json,
                    room,
                    embed_blob,
                    f"{key}.npz",
                    now,
                ),
            )

        self._db.commit()
        entry = {
            "key": key,
            "label": label,
            "modality": modality,
            "sensory": sensory,
            "context": ctx,
            "pattern": fused,
            "motor": motor,
            "room": room,
            "valence": valence,
            "arousal": arousal,
            "count": count,
            "hits": int(existing["hits"]) if existing else 0,
            "tags": json.loads(tag_json),
        }
        if embed_blob and self._embedder:
            entry["embedding"] = self._embedder.decode_blob(embed_blob)
        self._promote_hot(entry)
        return entry

    def backfill_embeddings(self, *, limit: int = 80) -> int:
        """Indexa embeddings para recuerdos antiguos sin vector semántico."""
        if not self._embedder:
            return 0
        expected_bytes = (
            (self._embedder.embedding_dim or self._embedder.fallback_dim) * 4
        )
        rows = self._db.execute(
            """
            SELECT * FROM memories
            ORDER BY updated_at DESC LIMIT ?
            """,
            (limit * 3,),
        ).fetchall()
        n = 0
        for row in rows:
            blob = row["embedding"]
            if blob and len(blob) == expected_bytes:
                continue
            if n >= limit:
                break
            tags = json.loads(row["tags"] or "[]")
            text = self._embedder.memory_semantic_text(
                label=row["label"],
                modality=row["modality"],
                room=row["room"] or "",
                tags=tags,
            )
            blob = self._embedder.encode_blob(self._embedder.embed(text))
            self._db.execute(
                "UPDATE memories SET embedding = ? WHERE key = ?",
                (blob, row["key"]),
            )
            n += 1
        if n:
            self._db.commit()
            self._load_hot_from_db()
        return n

    def _replay_weight(
        self,
        row: sqlite3.Row,
        now: float,
        *,
        sleep_pressure: float = 0.0,
        modulators: Any | None = None,
        sleep_phase: str = "",
        replay_mode: str = "default",
    ) -> float:
        """Prioridad de replay: recencia + emoción + repetición + tag consciente."""
        mode = (replay_mode or "default").strip().lower()
        if mode == "uniform":
            return 1.0

        valence = float(row["valence"])
        arousal = float(row["arousal"])
        count = int(row["count"])
        age_h = max(0.0, (now - float(row["updated_at"])) / 3600.0)

        recency = math.exp(-age_h / 18.0)
        emotional = 0.22 + 0.78 * min(abs(valence) * 0.65 + arousal * 0.55, 1.0)
        repetition = math.log1p(count) / math.log1p(10.0)

        weight = 0.30 * recency + 0.40 * emotional + 0.30 * repetition

        # Selectivo: prioriza |valence| (consolidación emocional) sin elegir acciones.
        if mode in ("selective", "emotion", "emotional"):
            weight *= 0.35 + 1.65 * min(abs(valence), 1.0)
            if sleep_phase == "rem":
                weight *= 1.15 + 0.25 * abs(valence)
            elif sleep_phase == "nrem_deep":
                weight *= 1.05 + 0.2 * abs(valence)

        tags = json.loads(row["tags"] or "[]")
        if "conscious" in tags:
            weight *= 1.48
            if sleep_phase == "rem":
                weight *= 1.22
            elif sleep_phase.startswith("nrem"):
                weight *= 1.12
        if "emotional" in tags or "affect" in tags:
            weight *= 1.35 if mode.startswith("select") else 1.1

        if sleep_pressure > 0.45:
            weight *= 0.80 + 0.35 * emotional
        if sleep_pressure > 0.75:
            weight *= 0.85 + 0.25 * recency

        if modulators is not None:
            ach = float(getattr(modulators, "acetylcholine", 0.5))
            cort = float(getattr(modulators, "cortisol", 0.0))
            weight *= 0.88 + 0.24 * ach * recency
            if cort > 0.35 and valence < -0.1:
                weight *= 1.12 + 0.15 * cort

        return max(weight, 1e-6)

    def record_sleep_replay(self, key: str) -> None:
        """Consolidación NREM: refuerza engrama tras replay."""
        row = self._db.execute("SELECT count FROM memories WHERE key = ?", (key,)).fetchone()
        if not row:
            return
        now = time.time()
        self._db.execute(
            "UPDATE memories SET count = count + 1, updated_at = ? WHERE key = ?",
            (now, key),
        )
        self._db.commit()
        for mem in self._hot:
            if mem.get("key") == key:
                mem["count"] = int(mem.get("count", 1)) + 1
                break

    def active_forgetting_pass(
        self,
        *,
        max_abs_valence: float = 0.22,
        min_count: int = 1,
    ) -> int:
        """
        Olvido activo suave: reduce ``count`` de engramas poco emocionales.
        No borra claves; no afecta selección motora en vigilia.
        """
        rows = self._db.execute(
            "SELECT key, valence, count FROM memories"
        ).fetchall()
        n = 0
        now = time.time()
        for row in rows:
            if abs(float(row["valence"])) >= max_abs_valence:
                continue
            c = int(row["count"])
            if c <= min_count:
                continue
            self._db.execute(
                "UPDATE memories SET count = ?, updated_at = ? WHERE key = ?",
                (c - 1, now, row["key"]),
            )
            n += 1
            for mem in self._hot:
                if mem.get("key") == row["key"]:
                    mem["count"] = c - 1
                    break
        if n:
            self._db.commit()
        return n

    def set_memory_affect(
        self,
        *,
        query: str,
        valence: float,
        arousal: float = 0.55,
        extra_tags: list[str] | None = None,
    ) -> int:
        """Ajusta valence/arousal de memorias cuyo label/tags contienen ``query`` (E4)."""
        q = (query or "").lower().strip()
        if not q:
            return 0
        tokens = [t for t in q.split() if t.strip()]
        rows = self._db.execute("SELECT key, label, tags FROM memories").fetchall()
        n = 0
        for row in rows:
            lab = str(row["label"] or "").lower()
            tags = [str(t).lower() for t in json.loads(row["tags"] or "[]")]
            hit = any(t in lab or t in tags for t in tokens) or q in lab
            if not hit:
                continue
            new_tags = list(dict.fromkeys(tags + list(extra_tags or []) + ["emotional"]))
            self._db.execute(
                "UPDATE memories SET valence = ?, arousal = ?, tags = ? WHERE key = ?",
                (float(valence), float(arousal), json.dumps(new_tags), row["key"]),
            )
            n += 1
        if n:
            self._db.commit()
            self._load_hot_from_db()
        return n

    def sample_for_replay(
        self,
        *,
        sleep_pressure: float = 0.0,
        modulators: Any | None = None,
        pool_size: int = 280,
        sleep_phase: str = "",
        replay_mode: str = "default",
    ) -> dict | None:
        """Replay ponderado (NREM): emoción, recencia, repetición y episodios conscientes."""
        rows = self._db.execute(
            "SELECT * FROM memories ORDER BY updated_at DESC LIMIT ?",
            (max(pool_size, 32),),
        ).fetchall()
        if not rows:
            return None

        now = time.time()
        mode = (replay_mode or "default").strip().lower()
        weights = np.array(
            [
                self._replay_weight(
                    row,
                    now,
                    sleep_pressure=sleep_pressure,
                    modulators=modulators,
                    sleep_phase=sleep_phase,
                    replay_mode=mode,
                )
                for row in rows
            ],
            dtype=np.float64,
        )
        weights /= weights.sum()
        pick = int(np.random.choice(len(rows), p=weights))
        entry = self._row_to_entry(rows[pick], load_pattern=True)
        if entry:
            entry["replay_weight"] = round(float(weights[pick]), 4)
            entry["replay_mode"] = mode
        return entry

    def sample_random(self) -> dict | None:
        row = self._db.execute(
            "SELECT * FROM memories ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
        if not row:
            return None
        return self._row_to_entry(row, load_pattern=True)

    def list_recent(self, n: int = 8) -> list[dict]:
        rows = self._db.execute(
            """
            SELECT label, modality, count, valence, room
            FROM memories ORDER BY updated_at DESC LIMIT ?
            """,
            (n,),
        ).fetchall()
        return [
            {
                "label": r["label"],
                "modality": r["modality"],
                "count": r["count"],
                "valence": round(float(r["valence"]), 3),
                "room": r["room"] or "",
            }
            for r in rows
        ]

    def import_legacy(self, memories: list[dict]) -> int:
        imported = 0
        for mem in memories:
            key = mem.get("key")
            if not key:
                continue
            if self._db.execute(
                "SELECT 1 FROM memories WHERE key = ?", (key,)
            ).fetchone():
                continue
            self.store(
                key,
                np.asarray(mem["pattern"], dtype=np.float32),
                label=mem.get("label", "?"),
                modality=mem.get("modality", "text"),
                motor=list(mem.get("motor", [])),
                valence=float(mem.get("valence", 0)),
                arousal=float(mem.get("arousal", 0)),
                tags=list(mem.get("tags", [])),
                room=mem.get("room", ""),
            )
            imported += 1
        return imported

    def clear(self) -> None:
        self._hot.clear()
        self._db.execute("DELETE FROM memories")
        self._db.commit()
        for f in self.patterns_dir.glob("*.npz"):
            f.unlink(missing_ok=True)

    def close(self) -> None:
        if self._db:
            self._db.close()
            self._db = None
