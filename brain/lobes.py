"""
Rutas por lóbulos — occipital, temporal, parietal, frontal.

Cada banda alimenta el tálamo por separado; el olfato va directo al límbico (sin tálamo).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

from .encode import encode_text
from .vision import encode_visual

if TYPE_CHECKING:
    from .mind import InfantApeBrain

ROOM_ODORS: dict[str, tuple[str, float, float]] = {
    "cocina": ("comida, café", 0.55, 0.12),
    "baño": ("humedad, jabón", 0.15, -0.05),
    "dormitorio": ("tela, descanso", 0.25, 0.08),
    "sala": ("polvo, TV", 0.35, 0.0),
    "jardín": ("tierra, plantas", 0.5, 0.18),
    "escritorio": ("papel, madera", 0.3, 0.05),
}


@dataclass
class LobeRouter:
    """Compone entradas corticales por lóbulo."""

    last: dict[str, Any] = field(default_factory=dict)

    def _band(self, n: int) -> int:
        return max(16, n // 4)

    def _fit_band(self, vec: np.ndarray, band: int) -> np.ndarray:
        out = np.zeros(band, dtype=np.float32)
        v = np.asarray(vec, dtype=np.float32).ravel()
        n = min(band, v.size)
        if n:
            out[:n] = v[:n]
        m = float(out.max())
        if m > 1e-6:
            out /= m
        return np.clip(out, 0, 1)

    def _blend_band(self, primary: np.ndarray, extra: np.ndarray | None, band: int, extra_w: float = 0.35) -> np.ndarray:
        base = self._fit_band(primary, band)
        if extra is not None and extra.size:
            base = np.clip(base * (1.0 - extra_w) + self._fit_band(extra, band) * extra_w, 0, 1)
        return base

    def sniff(self, brain: InfantApeBrain) -> tuple[np.ndarray, dict[str, Any]]:
        """Olfato → vector límbico directo (bypass tálamo)."""
        room = brain.world.current_room()
        label, intensity, valence = ROOM_ODORS.get(room, ("ambiente neutro", 0.12, 0.0))
        if brain.world.tv_state.get("active"):
            intensity = float(np.clip(intensity + 0.15, 0, 1))
        if brain.world.web_state.get("active") and room == "escritorio":
            intensity = float(np.clip(intensity + 0.08, 0, 1))
        if brain.body.hunger > 0.55 and room == "cocina":
            intensity = float(np.clip(intensity + 0.25, 0, 1))
        n_l = brain.cortex.n_limbic
        vec = encode_text(f"olfato:{label}@{room}", n_l).astype(np.float32)
        vec *= intensity
        meta = {
            "label": label,
            "room": room,
            "intensity": round(intensity, 3),
            "valence_hint": round(valence, 3),
        }
        return vec, meta

    def route(
        self,
        brain: InfantApeBrain,
        *,
        world_raw: np.ndarray,
        vision: dict | None,
        temporal: np.ndarray,
        intero: np.ndarray,
        ambient: dict | None = None,
    ) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
        n = brain.n_sensory
        band = self._band(n)

        percepts = (vision or {}).get("percepts", []) or (vision or {}).get("foveal", [])
        occipital = self._fit_band(
            encode_visual(percepts, band),
            band,
        )
        if world_raw.size >= band:
            occipital = np.clip(occipital * 0.55 + world_raw[:band] * 0.45, 0, 1)

        hour = int((ambient or {}).get("hour", 12))
        mem_echo = ""
        if brain.hippocampus.size > 0:
            mem_echo = f"mem{brain.hippocampus.size}"
        tv = "tv_on" if brain.world.tv_state.get("active") else ""
        temporal_enc = encode_text(
            f"temporal:{hour}|{tv}|{mem_echo}|{brain.world.current_room()}", band
        ).astype(np.float32)
        if temporal.size:
            temporal_enc = np.clip(
                temporal_enc * 0.6 + self._fit_band(temporal, band) * 0.4, 0, 1
            )
        temporal_band = self._fit_band(temporal_enc, band)

        par = brain.atlas.parietal.integrate(brain)
        parietal = self._blend_band(
            encode_text(
                f"parietal:body{par['body_schema']:.2f}|space{par['spatial_coherence']:.2f}|"
                f"x{int(brain.world.agent_x)}y{int(brain.world.agent_y)}",
                band,
            ),
            intero,
            band,
        )

        delib = brain.deliberation.last
        frontal = self._fit_band(
            encode_text(
                f"frontal:{delib.choice_key or 'idle'}|{delib.choice or '—'}|"
                f"agency{delib.agency:.2f}",
                band,
            ),
            band,
        )

        olfactory, olf_meta = self.sniff(brain)

        padded = lambda v: np.pad(v, (0, max(0, n - v.size)))[:n]
        thalamic = brain.thalamus.relay(
            {
                "occipital": padded(occipital),
                "temporal": padded(temporal_band),
                "parietal": padded(parietal),
                "frontal": padded(frontal),
                "world": world_raw * 0.35,
                "time": temporal,
            }
        )

        activity = {
            "occipital": round(float(occipital.mean()), 3),
            "temporal": round(float(temporal_band.mean()), 3),
            "parietal": round(float(parietal.mean()), 3),
            "frontal": round(float(frontal.mean()), 3),
            "olfactory": round(float(olfactory.mean()), 3),
        }

        self.last = {
            "activity": activity,
            "olfaction": olf_meta,
            "bands": {"occipital": band, "temporal": band, "parietal": band, "frontal": band},
            "vectors": {
                "occipital": occipital.astype(np.float32),
                "temporal": temporal_band.astype(np.float32),
                "parietal": parietal.astype(np.float32),
                "frontal": frontal.astype(np.float32),
            },
        }
        return thalamic, olfactory, self.last

    def to_dict(self) -> dict:
        if not self.last:
            return {}
        out = {k: v for k, v in self.last.items() if k != "vectors"}
        return out
