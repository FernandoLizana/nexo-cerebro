"""Filesystem local memory store — one Being, isolated directory tree."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, Sequence

from services.being.store import BeingStore
from services.memory.local.models import (
    LOCAL_MEMORY_FORMAT,
    LocalMemoryEntry,
    MemoryKind,
    RelationshipEntry,
    new_record_id,
)
from services.memory.local.recall import (
    DEFAULT_RECALL_LIMIT,
    HARD_RECALL_CAP,
    MAX_PROMPT_CHARS,
    MemoryPolicyError,
    clamp_limit,
    context_for_prompt,
    rank_entries,
    refuse_wholesale_dump,
)

_SAFE_RECORD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class LocalMemoryStore:
    """Per-Being local memory under ``<memory_root>/{episodic,semantic,...}/``.

    Isolation is path-based: never crosses into another Being's tree.
    """

    KIND_DIRS = {
        MemoryKind.EPISODIC: "episodic",
        MemoryKind.SEMANTIC: "semantic",
        MemoryKind.RELATIONSHIP: "relationships",
        MemoryKind.SUMMARY: "summaries",
    }

    def __init__(self, memory_root: Path | str, *, being_id: str | None = None) -> None:
        self.memory_root = Path(memory_root).resolve()
        self.being_id = being_id
        self.memory_root.mkdir(parents=True, exist_ok=True)
        for dirname in self.KIND_DIRS.values():
            (self.memory_root / dirname).mkdir(parents=True, exist_ok=True)
        meta = self.memory_root / "meta.json"
        if not meta.is_file():
            _write_json(
                meta,
                {
                    "format_version": LOCAL_MEMORY_FORMAT,
                    "being_id": being_id,
                    "layer": "LOCAL_MEMORY",
                },
            )

    @classmethod
    def for_being(cls, beings_root: Path | str, being_id: str) -> LocalMemoryStore:
        # Reuse BeingStore id + root containment checks (blocks ../ path escape).
        paths = BeingStore(beings_root).paths_for(being_id)
        return cls(paths.memory_dir, being_id=being_id)

    def _dir_for(self, kind: MemoryKind) -> Path:
        return self.memory_root / self.KIND_DIRS[kind]

    def _path_for(self, kind: MemoryKind, record_id: str) -> Path:
        raw = str(record_id or "").strip()
        if not _SAFE_RECORD_ID.fullmatch(raw) or ".." in raw:
            raise MemoryPolicyError("invalid record_id")
        path = (self._dir_for(kind) / f"{raw}.json").resolve()
        root = self.memory_root
        if path != root and root not in path.parents:
            raise MemoryPolicyError("memory path escapes store root")
        return path

    def add_episodic(
        self,
        content: str,
        *,
        importance: float = 0.5,
        confidence: float = 0.5,
        source: str = "local",
        tags: Sequence[str] | None = None,
    ) -> LocalMemoryEntry:
        entry = LocalMemoryEntry(
            record_id=new_record_id("ep"),
            kind=MemoryKind.EPISODIC,
            content=str(content),
            importance=importance,
            confidence=confidence,
            source=source,
            tags=list(tags or []),
        )
        self._write_entry(entry)
        return entry

    def add_semantic(
        self,
        content: str,
        *,
        importance: float = 0.6,
        confidence: float = 0.6,
        source: str = "local",
        tags: Sequence[str] | None = None,
    ) -> LocalMemoryEntry:
        entry = LocalMemoryEntry(
            record_id=new_record_id("sem"),
            kind=MemoryKind.SEMANTIC,
            content=str(content),
            importance=importance,
            confidence=confidence,
            source=source,
            tags=list(tags or []),
        )
        self._write_entry(entry)
        return entry

    def add_summary(
        self,
        content: str,
        *,
        importance: float = 0.7,
        confidence: float = 0.5,
        source: str = "local",
    ) -> LocalMemoryEntry:
        entry = LocalMemoryEntry(
            record_id=new_record_id("sum"),
            kind=MemoryKind.SUMMARY,
            content=str(content),
            importance=importance,
            confidence=confidence,
            source=source,
        )
        self._write_entry(entry)
        return entry

    def upsert_relationship(
        self,
        peer_being_id: str,
        *,
        relation_type: str = "known",
        strength: float = 0.5,
        notes: str = "",
        importance: float = 0.5,
        confidence: float = 0.5,
        source: str = "local",
    ) -> RelationshipEntry:
        peer = str(peer_being_id).strip()
        if not peer:
            raise ValueError("peer_being_id required")
        existing = self.find_relationship(peer, relation_type=relation_type)
        if existing is not None:
            existing.strength = max(0.0, min(1.0, float(strength)))
            existing.notes = str(notes)
            existing.importance = float(importance)
            existing.confidence = float(confidence)
            existing.source = source
            self._write_relationship(existing)
            return existing
        rel = RelationshipEntry(
            record_id=new_record_id("rel"),
            peer_being_id=peer,
            relation_type=str(relation_type or "known"),
            strength=strength,
            notes=notes,
            importance=importance,
            confidence=confidence,
            source=source,
        )
        self._write_relationship(rel)
        return rel

    def find_relationship(
        self, peer_being_id: str, *, relation_type: str | None = None
    ) -> RelationshipEntry | None:
        for rel in self.list_relationships():
            if rel.peer_being_id != peer_being_id:
                continue
            if relation_type is not None and rel.relation_type != relation_type:
                continue
            return rel
        return None

    def _write_entry(self, entry: LocalMemoryEntry) -> None:
        path = self._path_for(entry.kind, entry.record_id)
        _write_json(path, entry.to_dict())
        self._touch_index()

    def _write_relationship(self, rel: RelationshipEntry) -> None:
        path = self._path_for(MemoryKind.RELATIONSHIP, rel.record_id)
        _write_json(path, rel.to_dict())
        self._touch_index()

    def list_entries(self, kind: MemoryKind) -> list[LocalMemoryEntry]:
        if kind == MemoryKind.RELATIONSHIP:
            raise ValueError("use list_relationships() for relationship kind")
        out: list[LocalMemoryEntry] = []
        for path in sorted(self._dir_for(kind).glob("*.json")):
            data = _read_json(path)
            entry = LocalMemoryEntry.from_dict(data)
            if entry.kind != kind:
                entry.kind = kind
            out.append(entry)
        return out

    def list_relationships(self) -> list[RelationshipEntry]:
        out: list[RelationshipEntry] = []
        for path in sorted(self._dir_for(MemoryKind.RELATIONSHIP).glob("*.json")):
            out.append(RelationshipEntry.from_dict(_read_json(path)))
        return out

    def all_scored(self) -> list[LocalMemoryEntry | RelationshipEntry]:
        items: list[LocalMemoryEntry | RelationshipEntry] = []
        for kind in (MemoryKind.EPISODIC, MemoryKind.SEMANTIC, MemoryKind.SUMMARY):
            items.extend(self.list_entries(kind))
        items.extend(self.list_relationships())
        return items

    def count(self) -> int:
        return len(self.all_scored())

    def apply_decay(self, amount: float = 0.05, *, prune_threshold: float = 0.98) -> dict:
        """Increase decay; important memories decay slower. Prune near-forgotten low-importance."""
        amount = max(0.0, min(1.0, float(amount)))
        pruned = 0
        touched = 0
        for entry in self.list_entries(MemoryKind.EPISODIC) + self.list_entries(
            MemoryKind.SEMANTIC
        ) + self.list_entries(MemoryKind.SUMMARY):
            slow = 1.0 - (0.5 * max(0.0, min(1.0, entry.importance)))
            entry.decay = min(1.0, entry.decay + amount * slow)
            touched += 1
            if entry.decay >= prune_threshold and entry.importance < 0.25:
                self._path_for(entry.kind, entry.record_id).unlink(missing_ok=True)
                pruned += 1
            else:
                self._write_entry(entry)
        for rel in self.list_relationships():
            slow = 1.0 - (0.5 * max(0.0, min(1.0, rel.importance)))
            rel.decay = min(1.0, rel.decay + amount * slow)
            touched += 1
            if rel.decay >= prune_threshold and rel.importance < 0.25:
                self._path_for(MemoryKind.RELATIONSHIP, rel.record_id).unlink(missing_ok=True)
                pruned += 1
            else:
                self._write_relationship(rel)
        self._touch_index()
        return {"touched": touched, "pruned": pruned, "amount": amount}

    def recall(
        self,
        query: str | None = None,
        *,
        kinds: Iterable[MemoryKind] | None = None,
        limit: int = DEFAULT_RECALL_LIMIT,
        bump_recall: bool = True,
    ) -> list[LocalMemoryEntry | RelationshipEntry]:
        """Ranked recall with hard cap — never returns the full store beyond HARD_RECALL_CAP."""
        lim = clamp_limit(limit)
        allow = set(kinds) if kinds is not None else {
            MemoryKind.EPISODIC,
            MemoryKind.SEMANTIC,
            MemoryKind.SUMMARY,
            MemoryKind.RELATIONSHIP,
        }
        pool: list[LocalMemoryEntry | RelationshipEntry] = []
        if MemoryKind.EPISODIC in allow:
            pool.extend(self.list_entries(MemoryKind.EPISODIC))
        if MemoryKind.SEMANTIC in allow:
            pool.extend(self.list_entries(MemoryKind.SEMANTIC))
        if MemoryKind.SUMMARY in allow:
            pool.extend(self.list_entries(MemoryKind.SUMMARY))
        if MemoryKind.RELATIONSHIP in allow:
            pool.extend(self.list_relationships())
        ranked = rank_entries(pool, query=query)[:lim]
        if bump_recall:
            for item in ranked:
                item.recall_count = int(item.recall_count) + 1
                if isinstance(item, RelationshipEntry):
                    self._write_relationship(item)
                else:
                    self._write_entry(item)
        return ranked

    def prompt_context(
        self,
        query: str | None = None,
        *,
        limit: int = DEFAULT_RECALL_LIMIT,
        max_chars: int = MAX_PROMPT_CHARS,
    ) -> str:
        """Safe LLM-facing path: ranked + char-budgeted. Never dumps wholesale."""
        selected = self.recall(query, limit=clamp_limit(limit), bump_recall=True)
        return context_for_prompt(selected, limit=limit, max_chars=max_chars)

    def export_for_science(self, *, for_llm: bool = False) -> list[dict]:
        """Full export for offline analysis only. Refuses if marked for_llm."""
        records = self.all_scored()
        refuse_wholesale_dump(for_llm=for_llm, total_records=len(records))
        if for_llm:
            raise MemoryPolicyError("export_for_science cannot be used for LLM context")
        return [r.to_dict() for r in records]

    def rebuild_bundle_index(self) -> dict:
        """Write ``index.json`` compatible with Being MemoryBundle shape."""
        from services.being.models import MemoryBundle, MemoryRecord

        def to_record(entry: LocalMemoryEntry) -> MemoryRecord:
            return MemoryRecord(
                record_id=entry.record_id,
                content=entry.content,
                importance=entry.importance,
                confidence=entry.confidence,
                timestamp=entry.timestamp,
                source=entry.source,
                decay=entry.decay,
                recall_count=entry.recall_count,
            )

        bundle = MemoryBundle(
            episodic=[to_record(e) for e in self.list_entries(MemoryKind.EPISODIC)],
            semantic=[to_record(e) for e in self.list_entries(MemoryKind.SEMANTIC)],
            relationships=[r.to_dict() for r in self.list_relationships()],
            summaries=[to_record(e) for e in self.list_entries(MemoryKind.SUMMARY)],
        )
        payload = bundle.to_dict()
        _write_json(self.memory_root / "index.json", payload)
        return payload

    def _touch_index(self) -> None:
        try:
            self.rebuild_bundle_index()
        except Exception:
            # Index is convenience for BeingStore; file records remain source of truth.
            pass

    def stats(self) -> dict:
        return {
            "being_id": self.being_id,
            "format_version": LOCAL_MEMORY_FORMAT,
            "episodic": len(self.list_entries(MemoryKind.EPISODIC)),
            "semantic": len(self.list_entries(MemoryKind.SEMANTIC)),
            "relationships": len(self.list_relationships()),
            "summaries": len(self.list_entries(MemoryKind.SUMMARY)),
            "total": self.count(),
            "recall_default_limit": DEFAULT_RECALL_LIMIT,
            "recall_hard_cap": HARD_RECALL_CAP,
            "prompt_max_chars": MAX_PROMPT_CHARS,
        }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
