"""
Reflejos del tronco encefálico — orientación, alerta, funciones vitales.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class BrainstemReflexes:
    """Mesencéfalo, puente y bulbo modulan alerta y orientación."""

    orienting: float = 0.0
    startle: float = 0.0
    last_events: list[str] = field(default_factory=list)

    def step(
        self,
        brain,
        *,
        surprise: float = 0.0,
        vision: dict | None = None,
    ) -> dict[str, Any]:
        pain = brain.body.total_pain()
        events: list[str] = []

        if surprise > 0.45:
            self.startle = float(np.clip(self.startle * 0.5 + surprise * 0.55, 0, 1))
            brain.amygdala.arousal = float(np.clip(brain.amygdala.arousal + 0.12 * surprise, 0, 1))
            brain.modulators.norepinephrine = float(
                np.clip(brain.modulators.norepinephrine + 0.08 * surprise, 0, 1)
            )
            events.append("reflejo de alerta (mesencéfalo)")

        fix = (vision or {}).get("fixation") or {}
        sal = float(fix.get("salience", 0) or fix.get("interest", 0))
        if sal > 0.55:
            self.orienting = float(np.clip(self.orienting * 0.6 + sal * 0.45, 0, 1))
            tx, ty = fix.get("x"), fix.get("y")
            if tx is not None and ty is not None:
                brain.world.point_attention(float(tx), float(ty))
            events.append("orientación visual")

        if pain > 0.35:
            brain.brainstem.arousal_bias = float(np.clip(brain.brainstem.arousal_bias + 0.04, 0.2, 0.85))
            events.append("reflejo nociceptivo (bulbo)")

        if brain.brainstem.sleep_pressure > 0.72:
            brain.modulators.acetylcholine = float(
                np.clip(brain.modulators.acetylcholine * 0.97, 0.15, 1)
            )
            events.append("puente modula sueño")

        self.last_events = events[:6]
        stem_state = brain.atlas.brainstem.step(brain, surprise=surprise)
        return {
            "orienting": round(self.orienting, 3),
            "startle": round(self.startle, 3),
            "events": self.last_events,
            "brainstem": stem_state,
        }

    def to_dict(self) -> dict:
        return {
            "orienting": round(self.orienting, 3),
            "startle": round(self.startle, 3),
            "events": self.last_events[:4],
        }
