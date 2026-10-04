"""
Química social par a par: oxitocina, dopamina, atracción Nexo ↔ Nira.

No scripts de romance — solo señales acumuladas por proximidad, valencia social
y moduladores compartidos (VTA, hipotálamo).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class PeerBond:
    """Estado químico del vínculo entre Nexo y su compañera."""

    proximity: float = 0.0
    attraction: float = 0.42
    nexo_oxytocin: float = 0.35
    nira_oxytocin: float = 0.35
    dopamine_spike: float = 0.0
    last_social_valence: float = 0.0
    social_arousal: float = 0.0
    ticks_near: int = 0
    _ema_attraction: float = field(default=0.42, init=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "proximity": round(self.proximity, 3),
            "attraction": round(self.attraction, 3),
            "nexo_oxytocin": round(self.nexo_oxytocin, 3),
            "nira_oxytocin": round(self.nira_oxytocin, 3),
            "dopamine_spike": round(self.dopamine_spike, 3),
            "last_social_valence": round(self.last_social_valence, 3),
            "social_arousal": round(self.social_arousal, 3),
            "seek_companion": round(self.seek_companion_drive(), 3),
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> PeerBond:
        if not data:
            return cls()
        b = cls()
        b.proximity = float(data.get("proximity", 0))
        b.attraction = float(data.get("attraction", 0.42))
        b.nexo_oxytocin = float(data.get("nexo_oxytocin", 0.35))
        b.nira_oxytocin = float(data.get("nira_oxytocin", 0.35))
        b.dopamine_spike = float(data.get("dopamine_spike", 0))
        b.last_social_valence = float(data.get("last_social_valence", 0))
        b.social_arousal = float(data.get("social_arousal", 0))
        b._ema_attraction = b.attraction
        return b

    def update_proximity(self, distance: float, *, near_threshold: float = 90.0) -> None:
        self.proximity = float(np.clip(1.0 - distance / max(near_threshold, 1.0), 0, 1))
        if self.proximity > 0.45:
            self.ticks_near += 1
            release = 0.004 + 0.012 * self.proximity
            self.nexo_oxytocin = float(np.clip(self.nexo_oxytocin + release, 0, 1))
            self.nira_oxytocin = float(np.clip(self.nira_oxytocin + release * 0.95, 0, 1))
        else:
            self.ticks_near = max(0, self.ticks_near - 1)

    def on_social_episode(
        self,
        *,
        valence: float,
        arousal: float,
        dopamine: float,
        proximity: float | None = None,
    ) -> None:
        """Pico tras episodio social (corteza + amígdala ya evaluaron)."""
        self.last_social_valence = float(valence)
        self.social_arousal = float(arousal)
        if proximity is not None:
            self.proximity = float(proximity)
        pos = max(0.0, valence)
        oxy_bump = 0.02 + 0.08 * pos * self.proximity + 0.03 * arousal * self.proximity
        self.nexo_oxytocin = float(np.clip(self.nexo_oxytocin + oxy_bump, 0, 1))
        self.nira_oxytocin = float(np.clip(self.nira_oxytocin + oxy_bump * 0.92, 0, 1))
        self.dopamine_spike = float(np.clip(0.35 * dopamine + 0.25 * pos + 0.15 * arousal, 0, 1))
        self._integrate_attraction()

    def decay(self) -> None:
        self.dopamine_spike = float(np.clip(self.dopamine_spike * 0.88, 0, 1))
        if self.proximity < 0.2:
            self.nexo_oxytocin = float(np.clip(self.nexo_oxytocin * 0.998, 0, 1))
            self.nira_oxytocin = float(np.clip(self.nira_oxytocin * 0.998, 0, 1))
        self._integrate_attraction()

    def _integrate_attraction(self) -> None:
        raw = (
            0.32 * self.nexo_oxytocin
            + 0.28 * self.nira_oxytocin
            + 0.18 * self.proximity
            + 0.12 * max(0.0, self.last_social_valence)
            + 0.10 * self.dopamine_spike
        )
        self._ema_attraction = float(np.clip(0.82 * self._ema_attraction + 0.18 * raw, 0, 1))
        self.attraction = self._ema_attraction

    def seek_companion_drive(self) -> float:
        """Impulso de acercarse — sube con oxitocina y baja si ya están pegados."""
        if self.proximity > 0.75:
            return float(np.clip(0.08 * self.attraction, 0, 0.25))
        base = 0.15 * self.nexo_oxytocin + 0.12 * self.attraction
        lonely = max(0.0, 0.55 - self.proximity)
        return float(np.clip(base * lonely + 0.05 * self.dopamine_spike, 0, 1))

    def sync_to_hypothalamus(self, hypothalamus) -> None:
        hypothalamus.oxytocin = float(
            np.clip(0.55 * hypothalamus.oxytocin + 0.45 * self.nexo_oxytocin, 0, 1)
        )

    def sync_persona_attachment(self, persona, companion_persona) -> None:
        persona.attachment = float(
            np.clip(0.6 * persona.attachment + 0.4 * self.attraction, 0, 1)
        )
        companion_persona.attachment = float(
            np.clip(0.6 * companion_persona.attachment + 0.4 * self.attraction * 0.95, 0, 1)
        )

    def companion_mood_from_body(self, comfort: float, drives: dict) -> str:
        """Ánimo de Nira desde interocepción + química, no plantillas."""
        if drives.get("seek_food", 0) > 0.55 or drives.get("seek_bathroom", 0) > 0.5:
            return "stressed"
        if self.proximity > 0.5 and self.last_social_valence > 0.15:
            return "content"
        if self.attraction > 0.55 and self.proximity < 0.3:
            return "curious"
        if comfort > 0.58:
            return "calm"
        if comfort < 0.38:
            return "uneasy"
        return "calm"
