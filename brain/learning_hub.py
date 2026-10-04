"""
Hub unificado de aprendizaje — toda interacción deja huella en memoria.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

from .encode import encode_text
from .library import list_books, read_book
from .text_extract import extract_plain_text

if TYPE_CHECKING:
    from .mind import InfantApeBrain

CHUNK_SIZE = 620
MAX_CHUNKS = 3
CURRICULUM_CHUNK_SIZE = 720
CURRICULUM_MAX_CHUNKS = 8


@dataclass
class LearningEvent:
    source: str
    label: str
    content: str
    modality: str = "text"
    tags: list[str] = field(default_factory=list)
    agents: list[str] = field(default_factory=lambda: ["nexo"])
    social: bool = False
    steps_per_repeat: int = 32


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text) and len(chunks) < MAX_CHUNKS + 2:
        end = min(len(text), start + size)
        if end < len(text):
            break_at = text.rfind(" ", start, end)
            if break_at > start + size // 3:
                end = break_at
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        start = end
    return chunks[:MAX_CHUNKS]


class LearningHub:
    def __init__(self) -> None:
        self.recent: list[dict] = []

    def learn(self, brain: InfantApeBrain, event: LearningEvent) -> dict:
        if event.source == "curriculum":
            chunks = chunk_text(event.content, size=CURRICULUM_CHUNK_SIZE)[:CURRICULUM_MAX_CHUNKS]
        elif event.source == "brain_facts":
            chunks = chunk_text(event.content, size=1100)[:14]
        else:
            chunks = chunk_text(event.content)
        if not chunks:
            chunks = [event.label[:200] or event.source]

        mult = max(1.0, brain.learning_multiplier())
        base_steps = int(max(8, round(event.steps_per_repeat * mult)))
        if event.source in ("curriculum", "brain_facts", "google", "web"):
            chunks = chunks[: min(len(chunks), int(3 + mult))]

        episodes: list[dict] = []
        agents = event.agents or ["nexo"]
        shared = "nira" in agents and "nexo" in agents

        for i, chunk in enumerate(chunks):
            chunk_label = f"{event.label[:70]} ·{i + 1}" if len(chunks) > 1 else event.label[:80]
            tags = [*event.tags, event.source, f"chunk:{i + 1}"]

            if "nexo" in agents:
                ep = self._episode_for_agent(
                    brain,
                    chunk,
                    label=chunk_label,
                    modality=event.modality,
                    tags=[*tags, "actor:nexo"],
                    social=event.social,
                    steps=base_steps,
                )
                episodes.append({"agent": "nexo", "episode": ep, "chunk": chunk[:80]})

            if "nira" in agents:
                ep_n = self._episode_for_agent(
                    brain,
                    chunk,
                    label=f"Nira·{chunk_label}",
                    modality="social" if event.social else event.modality,
                    tags=[*tags, "actor:nira"],
                    social=True,
                    steps=max(18, base_steps // 2),
                    as_companion=True,
                )
                episodes.append({"agent": "nira", "episode": ep_n, "chunk": chunk[:80]})
                brain.companion.persona.learned.append(
                    {"label": chunk_label[:50], "source": event.source, "snippet": chunk[:100]}
                )
                if len(brain.companion.persona.learned) > 24:
                    brain.companion.persona.learned.pop(0)

            self._maybe_ingest_virtual(brain, chunk, chunk_label, event, episodes[-1]["episode"] if episodes else None)

        remembered = any(e["episode"].get("remembered") for e in episodes)
        entry = {
            "source": event.source,
            "label": event.label[:80],
            "agents": agents,
            "shared": shared,
            "chunks": len(chunks),
            "remembered": remembered,
        }
        self.recent.insert(0, entry)
        self.recent = self.recent[:12]
        brain._learning_log.insert(0, f"aprendió ({event.source}): {event.label[:50]}")
        brain._learning_log = brain._learning_log[:10]
        out: dict[str, Any] = {
            "learned": entry,
            "episodes": len(episodes),
            "chunks": chunks,
            "episode_list": episodes,
        }
        # Nexus active cycle: verified only when episode evidence stuck in memory.
        try:
            from .dyad_learning import nexus_active_step

            nexus_rec = nexus_active_step(
                goal=f"learn:{event.source}",
                hypothesis=event.label[:120],
                observation=(
                    f"chunks={len(chunks)} remembered={remembered} "
                    f"source={event.source}"
                ),
                authorized=True,
                evidence_ok=bool(remembered),
            )
            out["dyad_learning"] = nexus_rec.to_dict()
            out["nexus_learning"] = nexus_rec.to_dict()
            log = getattr(brain, "_nexus_dyad_log", None)
            if not isinstance(log, list):
                log = []
            log.insert(0, nexus_rec.to_dict())
            brain._nexus_dyad_log = log[:24]
        except ImportError:
            pass
        except Exception:
            out["dyad_learning"] = {"error": True, "actor": "nexus"}
        return out

    def _episode_for_agent(
        self,
        brain: InfantApeBrain,
        chunk: str,
        *,
        label: str,
        modality: str,
        tags: list[str],
        social: bool,
        steps: int,
        as_companion: bool = False,
    ) -> dict:
        pattern = encode_text(chunk, brain.n_sensory)
        relay_key = modality if modality in ("text", "document", "video", "social", "world") else "text"
        packet: dict = {relay_key: pattern}
        if not as_companion:
            packet["world"] = brain._world_sensory_vector()
        sensory = brain.thalamus.relay(packet)
        return brain._run_episode(
            sensory,
            modality=modality,
            label=label,
            repeats=1,
            steps_per_repeat=steps,
            social=social or as_companion,
            tags=tags,
        )

    def _maybe_ingest_virtual(
        self,
        brain: InfantApeBrain,
        chunk: str,
        label: str,
        event: LearningEvent,
        ep: dict | None,
    ) -> None:
        if not ep:
            return
        novelty = 0.85 if not ep.get("remembered") else 0.35
        if novelty < 0.4 and ep.get("arousal", 0) < 0.35:
            return
        pattern = encode_text(chunk, brain.n_sensory)
        brain.virtual_store.ingest(
            pattern,
            label=label[:60],
            modality=event.modality,
            valence=float(ep.get("valence", 0)),
            arousal=float(ep.get("arousal", 0.3)),
            strength=min(1.0, 0.45 + novelty * 0.4),
        )

    def resolve_book_content(self, brain: InfantApeBrain, ev: dict) -> tuple[str, str]:
        label = str(ev.get("label", "libro"))
        meta = ev.get("meta") or {}
        lib_path = meta.get("library_path") or meta.get("path") or ""
        memory_key = str(ev.get("memory_key") or "")

        candidates = [
            p
            for p in (lib_path, memory_key)
            if p and ("/" in p or p.endswith((".txt", ".pdf", ".epub", ".md")))
        ]
        for path in candidates:
            try:
                data, fn = read_book(path)
                text = extract_plain_text(data, fn)
                if text.strip():
                    return text, label
            except Exception:
                continue

        for book in list_books():
            if book["name"].lower() in label.lower() or label.lower() in book["name"].lower():
                try:
                    data, fn = read_book(book["path"])
                    text = extract_plain_text(data, fn)
                    if text.strip():
                        return text, book["name"]
                except Exception:
                    continue

        if memory_key:
            row = brain.memory_store._db.execute(
                "SELECT label FROM memories WHERE key = ?", (memory_key,)
            ).fetchone()
            if row:
                return f"Recuerdo del libro «{row['label']}». Fragmento asociado en memoria.", row["label"]

        return f"Leaf through «{label}» — text not fully loaded.", label

    def agents_near_tv(self, brain: InfantApeBrain, radius: float = 62.0) -> list[str]:
        fu = brain.world._furniture("tv")
        if not fu:
            return ["nexo"]
        cx, cy = fu.x + fu.w / 2, fu.y + fu.h / 2
        agents = []
        if float(np.hypot(cx - brain.world.agent_x, cy - brain.world.agent_y)) < radius:
            agents.append("nexo")
        if float(np.hypot(cx - brain.companion.x, cy - brain.companion.y)) < radius:
            agents.append("nira")
        return agents or ["nexo"]

    def snapshot(self) -> list[dict]:
        return list(self.recent)
