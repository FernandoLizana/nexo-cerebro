"""Contestantes de acción — competencia límbica vs PFC."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ActionContestant:
    key: str
    label: str
    drive: str
    limbic: float = 0.0
    pfc: float = 0.0
    habit: float = 0.0
    net: float = 0.0
    selected: bool = False


@dataclass
class DeliberationResult:
    choice_key: str = "rest"
    confidence: float = 0.25
    conflict: float = 0.0
    limbic_winner_key: str = ""
    pfc_winner_key: str = ""
    inhibited: bool = False
    pfc_veto: bool = False
    contestants: list[ActionContestant] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return {
            "choice_key": self.choice_key,
            "confidence": round(self.confidence, 4),
            "conflict": round(self.conflict, 4),
            "limbic_winner_key": self.limbic_winner_key,
            "pfc_winner_key": self.pfc_winner_key,
            "inhibited": self.inhibited,
            "pfc_veto": self.pfc_veto,
            "contestants": [
                {
                    "key": c.key,
                    "limbic": round(c.limbic, 4),
                    "pfc": round(c.pfc, 4),
                    "habit": round(c.habit, 4),
                    "net": round(c.net, 4),
                    "selected": c.selected,
                }
                for c in self.contestants[:6]
            ],
        }
