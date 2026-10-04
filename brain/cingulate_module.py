"""
Cíngulo — monitoreo de conflicto, error y esfuerzo (Brain Facts: Thinking, pain).

Señala a la prefrontal cuando hay que re-deliberar o ajustar conducta.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .mind import InfantApeBrain


@dataclass
class CingulateMonitor:
    conflict_level: float = 0.0
    error_signal: float = 0.0
    motivational_drive: float = 0.0

    def integrate(self, brain: InfantApeBrain, *, surprise: float = 0.0) -> dict[str, Any]:
        cog = brain.cognition.last_summary or {}
        decision = cog.get("decision") or {}
        conflict = float(decision.get("conflict", cog.get("conflict", 0.2)))
        delib = brain.deliberation.last
        limbic_gap = 0.0
        if delib.limbic_winner and delib.choice_key and delib.limbic_winner != delib.choice_key:
            limbic_gap = 0.35

        self.conflict_level = float(np.clip(conflict + surprise * 0.4 + limbic_gap, 0, 1))
        self.error_signal = float(np.clip(surprise * 0.55 + (0.25 if delib.inhibited else 0), 0, 1))
        self.motivational_drive = float(
            np.clip(0.3 + delib.agency * 0.35 + brain.modulators.dopamine * 0.25, 0, 1)
        )

        if self.conflict_level > 0.5:
            brain.modulators.norepinephrine = float(
                np.clip(brain.modulators.norepinephrine + 0.03 * self.conflict_level, 0, 1)
            )
            brain.deliberation.last.conflict = max(brain.deliberation.last.conflict, self.conflict_level)

        should_redeliberate = self.error_signal > 0.45 and self.conflict_level > 0.42

        return {
            "conflict_level": round(self.conflict_level, 3),
            "error_signal": round(self.error_signal, 3),
            "motivational_drive": round(self.motivational_drive, 3),
            "should_redeliberate": should_redeliberate,
        }
