"""
Colículo superior — mapa espacial audiovisual unificado.

Fusiona ángulo/distancia visión + dirección auditiva para saliencia espacial.
No elige acciones — sesga atención bottom-up.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class SuperiorColliculus:
    """Mapa retinotópico + auditivo 2D simplificado."""

    map_size: int = 8
    activity: np.ndarray = field(default_factory=lambda: np.zeros((8, 8), dtype=np.float32))
    peak_azimuth: float = 0.0
    peak_elevation: float = 0.0
    peak_salience: float = 0.0
    last_sources: list[str] = field(default_factory=list)

    def _idx(self, angle_deg: float, distance: float) -> tuple[int, int]:
        # azimuth -90..90 → col; distance → row (cerca arriba)
        col = int(np.clip((angle_deg + 90) / 22.5, 0, self.map_size - 1))
        row = int(np.clip(distance / 18.0, 0, self.map_size - 1))
        return row, col

    def fuse(
        self,
        *,
        vision: dict | None,
        audio_meta: dict | None,
        vestibular_meta: dict | None = None,
    ) -> dict[str, Any]:
        self.activity *= 0.82
        sources: list[str] = []
        vision = vision or {}

        for p in (vision.get("foveal") or [])[:6]:
            ang = float(p.get("angle_deg", 0))
            dist = float(p.get("distance", 80))
            sal = float(p.get("salience", 0.3))
            r, c = self._idx(ang, dist)
            self.activity[r, c] = float(np.clip(self.activity[r, c] + sal * 0.45, 0, 1.5))
            sources.append(f"vis:{p.get('label', '?')[:20]}")

        if audio_meta and float(audio_meta.get("loudness", 0)) > 0.25:
            az = 0.0 if not audio_meta.get("caregiver") else -15.0
            r, c = self._idx(az, 55.0)
            loud = float(audio_meta.get("loudness", 0.3))
            self.activity[r, c] = float(np.clip(self.activity[r, c] + loud * 0.5, 0, 1.5))
            sources.append("aud:eco")

        if vestibular_meta and float(vestibular_meta.get("vertigo", 0)) > 0.35:
            self.activity[0, self.map_size // 2] = float(
                np.clip(self.activity[0, self.map_size // 2] + 0.35, 0, 1.2)
            )
            sources.append("vest:vertigo")

        flat_i = int(np.argmax(self.activity))
        r, c = divmod(flat_i, self.map_size)
        self.peak_salience = float(self.activity[r, c])
        self.peak_azimuth = float(c * 22.5 - 90)
        self.peak_elevation = float(r * 18)
        self.last_sources = sources[:6]

        return {
            "peak": {
                "azimuth_deg": round(self.peak_azimuth, 1),
                "distance_proxy": round(self.peak_elevation, 1),
                "salience": round(self.peak_salience, 3),
            },
            "sources": self.last_sources,
            "map_max": round(float(self.activity.max()), 3),
        }

    def encode(self, n: int) -> np.ndarray:
        flat = self.activity.ravel()
        if flat.size >= n:
            return flat[:n].astype(np.float32)
        return np.pad(flat, (0, n - flat.size)).astype(np.float32)

    def to_dict(self) -> dict[str, Any]:
        return {
            "peak_azimuth": round(self.peak_azimuth, 1),
            "peak_salience": round(self.peak_salience, 3),
            "sources": list(self.last_sources),
            "map_max": round(float(self.activity.max()), 3),
        }
