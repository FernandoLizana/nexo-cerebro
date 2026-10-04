"""Candidato al workspace global."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WorkspaceCandidate:
    source: str
    label: str
    salience: float
    modality: str = ""
    valence: float = 0.0
    action_hints: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, str | float | tuple[str, ...]]:
        return {
            "source": self.source,
            "label": self.label,
            "salience": round(self.salience, 4),
            "modality": self.modality,
            "valence": round(self.valence, 4),
            "action_hints": self.action_hints,
        }
