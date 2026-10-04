"""Bounded recall + prompt context (anti prompt-stuffing)."""

from __future__ import annotations

from typing import Iterable, Sequence

from services.memory.local.models import LocalMemoryEntry, RelationshipEntry

DEFAULT_RECALL_LIMIT = 8
HARD_RECALL_CAP = 32
MAX_PROMPT_CHARS = 1500


class MemoryPolicyError(ValueError):
    """Raised when a caller attempts unsafe wholesale memory injection."""


Scored = LocalMemoryEntry | RelationshipEntry


def rank_entries(entries: Iterable[Scored], *, query: str | None = None) -> list[Scored]:
    """Rank by effective score; optional case-insensitive substring boost."""
    q = (query or "").strip().lower()
    scored: list[tuple[float, Scored]] = []
    for entry in entries:
        score = float(entry.effective_score())
        if q:
            text = (
                entry.content()
                if isinstance(entry, RelationshipEntry)
                else str(entry.content)
            ).lower()
            if q in text:
                score += 0.25
            elif any(tok and tok in text for tok in q.split()):
                score += 0.1
            else:
                # No match → still eligible but demoted (caller may filter)
                score *= 0.15
        scored.append((score, entry))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [e for _, e in scored]


def clamp_limit(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_RECALL_LIMIT
    return max(1, min(HARD_RECALL_CAP, int(limit)))


def context_for_prompt(
    entries: Sequence[Scored],
    *,
    limit: int = DEFAULT_RECALL_LIMIT,
    max_chars: int = MAX_PROMPT_CHARS,
) -> str:
    """Build a bounded snippet for optional LLM context.

    Never includes the full store. Hard-caps entry count and character budget.
    """
    if max_chars < 32:
        raise MemoryPolicyError("max_chars too small for useful context")
    if max_chars > 8000:
        raise MemoryPolicyError("max_chars exceeds safe prompt budget (8000)")
    lim = clamp_limit(limit)
    if lim > HARD_RECALL_CAP:
        raise MemoryPolicyError("recall limit exceeds hard cap")

    parts: list[str] = []
    used = 0
    for entry in entries[:lim]:
        if isinstance(entry, RelationshipEntry):
            line = f"[rel/{entry.relation_type}] {entry.peer_being_id}: {entry.notes}".strip()
        else:
            line = f"[{entry.kind.value}] {entry.content}".strip()
        if not line:
            continue
        # Leave room for separators
        if used + len(line) + 1 > max_chars:
            remain = max_chars - used - 1
            if remain < 24:
                break
            line = line[:remain].rstrip() + "…"
            parts.append(line)
            break
        parts.append(line)
        used += len(line) + 1
    return "\n".join(parts)


def refuse_wholesale_dump(*, for_llm: bool, total_records: int) -> None:
    """Explicit guard used by store APIs that might be misused as dumpers."""
    if for_llm and total_records > HARD_RECALL_CAP:
        raise MemoryPolicyError(
            "refusing wholesale memory dump into LLM context; "
            f"use context_for_prompt (cap={HARD_RECALL_CAP})"
        )
