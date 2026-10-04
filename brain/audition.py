"""
Audición — eco del cuidador, TV y eventos sociales como bandas espectrales.

No elige acciones: alimenta tálamo temporal y hub multimodal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .encode import encode_text


@dataclass
class AuditoryPathway:
    """Pseudo-espectrograma: bajos (prosodia) / medios (fonemas) / agudos (ruido)."""

    last_echo: str = ""
    last_loudness: float = 0.0
    bands: dict[str, float] = field(default_factory=dict)
    caregiver_present: bool = False

    def _band_split(self, text: str, n: int) -> tuple[np.ndarray, dict[str, float]]:
        base = encode_text(text, n).astype(np.float32)
        third = max(1, n // 3)
        low = base[:third]
        mid = base[third : 2 * third]
        high = base[2 * third :]
        bands = {
            "low_hz": float(low.mean()),
            "mid_hz": float(mid.mean()),
            "high_hz": float(high.mean()),
        }
        return base, bands

    def listen(
        self,
        brain,
        *,
        echo: str | None = None,
        vision: dict | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        vision = vision or brain._last_vision or {}
        room = brain.world.current_room()
        parts: list[str] = []
        loudness = 0.12

        if echo:
            parts.append(echo[:120])
            loudness = 0.55
            self.last_echo = echo[:80]
        elif brain._pending_echo_glimmer:
            parts.append(str(brain._pending_echo_glimmer)[:80])
            loudness = 0.42

        if brain.world.tv_state.get("active"):
            title = str(brain.world.tv_state.get("title", "tv"))[:40]
            parts.append(f"tv:{title}")
            loudness = max(loudness, 0.38)

        caregiver = vision.get("caregiver") or {}
        self.caregiver_present = bool(caregiver.get("visible"))
        if self.caregiver_present:
            parts.append("voz_cuidador_cerca")
            loudness = max(loudness, 0.48)

        if brain.companion.bond_with_nexo > 0.45 and brain._companion_near(radius=90):
            parts.append(f"companion:{brain.companion.name}")
            loudness = max(loudness, 0.35)

        if not parts:
            parts.append(f"ambiente:{room}")

        text = "|".join(parts)
        n = brain.n_sensory
        pat, bands = self._band_split(text, n)
        pat *= float(np.clip(loudness, 0.08, 1.0))
        self.bands = bands
        self.last_loudness = loudness

        meta = {
            "echo": self.last_echo,
            "loudness": round(loudness, 3),
            "bands": {k: round(v, 3) for k, v in bands.items()},
            "caregiver": self.caregiver_present,
            "sources": parts[:4],
        }
        return pat, meta

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_echo": self.last_echo,
            "loudness": round(self.last_loudness, 3),
            "bands": self.bands,
            "caregiver_present": self.caregiver_present,
        }
