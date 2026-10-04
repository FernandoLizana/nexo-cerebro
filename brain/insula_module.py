"""
Ínsula — interocepción visceral (Brain Facts: Body in Balance, pain, emotion).

Integra señales corporales con afecto y red de saliencia.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .mind import InfantApeBrain


@dataclass
class InsulaCortex:
    interoceptive_salience: float = 0.0
    visceral_tone: float = 0.5
    empathy_bias: float = 0.0

    def integrate(self, brain: InfantApeBrain) -> dict[str, Any]:
        body = brain.body
        pain = body.total_pain()
        hunger = float(getattr(body, "hunger", 0.3))
        comfort = body.comfort
        cortisol = brain.hypothalamus.cortisol

        self.visceral_tone = float(
            np.clip(0.35 * comfort + 0.25 * (1 - hunger) + 0.2 * (1 - pain) + 0.2 * (1 - cortisol), 0, 1)
        )
        self.interoceptive_salience = float(
            np.clip(pain * 0.45 + (1 - comfort) * 0.3 + hunger * 0.2 + cortisol * 0.25, 0, 1)
        )
        caregiver = (brain._last_vision or {}).get("caregiver", {})
        self.empathy_bias = float(
            np.clip(0.15 + (0.35 if caregiver.get("visible") else 0) + brain.hypothalamus.oxytocin * 0.25, 0, 1)
        )

        if self.interoceptive_salience > 0.45:
            brain.amygdala.arousal = float(
                np.clip(brain.amygdala.arousal + 0.04 * self.interoceptive_salience, 0, 1)
            )
        if self.visceral_tone > 0.6:
            brain.modulators.serotonin = float(
                np.clip(brain.modulators.serotonin + 0.02, 0, 1)
            )

        return {
            "interoceptive_salience": round(self.interoceptive_salience, 3),
            "visceral_tone": round(self.visceral_tone, 3),
            "empathy_bias": round(self.empathy_bias, 3),
            "unified_feelings": self.unified_feelings(brain),
        }

    def unified_feelings(self, brain: InfantApeBrain) -> list[dict[str, Any]]:
        """Panel ínsula — integración visceral–afectiva."""
        items: list[dict[str, Any]] = []
        for f in brain.body.feelings()[:6]:
            items.append(
                {
                    "signal": f["signal"],
                    "intensity": round(float(f.get("intensity", 0)), 3),
                    "source": "interoception",
                }
            )
        pain = brain.body.total_pain()
        if pain > 0.12:
            items.append({"signal": "dolor", "intensity": round(pain, 3), "source": "nociception"})
        items.append(
            {
                "signal": "tono visceral",
                "intensity": round(self.visceral_tone, 3),
                "source": "insula",
            }
        )
        if self.empathy_bias > 0.35:
            items.append(
                {
                    "signal": "empatía social",
                    "intensity": round(self.empathy_bias, 3),
                    "source": "insula",
                }
            )
        return items[:8]
