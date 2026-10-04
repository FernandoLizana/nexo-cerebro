"""Simple associative memory — cue → response strength (no LLM)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AssociativeMemory:
    """Tiny associative store with decay and recall counts."""

    associations: dict[str, dict[str, float]] = field(default_factory=dict)
    recall_counts: dict[str, int] = field(default_factory=dict)

    def learn(self, cue: str, response: str, strength: float = 0.2) -> None:
        cue_key = cue.strip().lower()
        resp_key = response.strip().lower()
        if not cue_key or not resp_key:
            return
        bucket = self.associations.setdefault(cue_key, {})
        bucket[resp_key] = float(max(0.0, min(1.0, bucket.get(resp_key, 0.0) + strength)))

    def recall(self, cue: str) -> tuple[str | None, float]:
        cue_key = cue.strip().lower()
        bucket = self.associations.get(cue_key) or {}
        if not bucket:
            return None, 0.0
        response, strength = max(bucket.items(), key=lambda kv: kv[1])
        self.recall_counts[cue_key] = self.recall_counts.get(cue_key, 0) + 1
        return response, float(strength)

    def decay(self, factor: float = 0.02) -> None:
        factor = max(0.0, min(1.0, factor))
        for cue, bucket in list(self.associations.items()):
            for resp in list(bucket):
                bucket[resp] = max(0.0, bucket[resp] * (1.0 - factor))
                if bucket[resp] < 0.01:
                    del bucket[resp]
            if not bucket:
                del self.associations[cue]

    def to_dict(self) -> dict[str, Any]:
        return {
            "associations": {k: dict(v) for k, v in self.associations.items()},
            "recall_counts": dict(self.recall_counts),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> AssociativeMemory:
        data = dict(data or {})
        mem = cls()
        raw = dict(data.get("associations") or {})
        mem.associations = {str(k): {str(a): float(b) for a, b in dict(v).items()} for k, v in raw.items()}
        mem.recall_counts = {str(k): int(v) for k, v in dict(data.get("recall_counts") or {}).items()}
        return mem
