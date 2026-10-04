"""
Orquestador de percepción sensorial — Bloque C (items 21–32).

Integra audición, olfato, gusto, propiocepción, vestibular y colículo.
Sesga tálamo/sensory; nunca escribe choice_key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .audition import AuditoryPathway
from .experiment_flags import get_flags
from .gustation import GustatoryPathway
from .proprioception import ProprioceptivePathway
from .superior_colliculus import SuperiorColliculus
from .vestibular import VestibularPathway


@dataclass
class SensoryPerceptionStack:
    audition: AuditoryPathway = field(default_factory=AuditoryPathway)
    gustation: GustatoryPathway = field(default_factory=GustatoryPathway)
    proprioception: ProprioceptivePathway = field(default_factory=ProprioceptivePathway)
    vestibular: VestibularPathway = field(default_factory=VestibularPathway)
    colliculus: SuperiorColliculus = field(default_factory=SuperiorColliculus)
    last_channels: dict[str, Any] = field(default_factory=dict)

    def tick(
        self,
        brain,
        *,
        vision: dict | None = None,
        echo: str | None = None,
    ) -> dict[str, Any]:
        flags = get_flags(brain)
        if not flags.enable_advanced_sensory:
            return {}

        vision = vision or brain._last_vision or {}
        audio_pat, audio_meta = self.audition.listen(brain, echo=echo, vision=vision)
        taste_pat, taste_meta = self.gustation.sample(brain)
        prop_pat, prop_meta = self.proprioception.integrate(brain)
        vest_pat, vest_meta = self.vestibular.integrate(brain)

        sc_meta = {}
        if flags.enable_superior_colliculus:
            sc_meta = self.colliculus.fuse(
                vision=vision,
                audio_meta=audio_meta,
                vestibular_meta=vest_meta,
            )

        if flags.enable_cardiac_interoception:
            brain.body.update_baroreceptors(brain.biomech.heart_rate)

        if flags.enable_referred_pain:
            brain.nociceptor.apply_referred_pain(brain.body)

        self.last_channels = {
            "audition": audio_meta,
            "gustation": taste_meta,
            "proprioception": prop_meta,
            "vestibular": vest_meta,
            "colliculus": sc_meta,
            "olfaction": (brain.lobes.last or {}).get("olfaction", {}),
        }
        return {
            "audio_pat": audio_pat,
            "taste_pat": taste_pat,
            "prop_pat": prop_pat,
            "vest_pat": vest_pat,
            "sc_pat": self.colliculus.encode(max(8, brain.n_sensory // 24)),
            "meta": self.last_channels,
        }

    def blend_sensory(
        self,
        brain,
        sensory: np.ndarray,
        *,
        stack: dict[str, Any],
    ) -> np.ndarray:
        if not stack:
            return sensory
        n = sensory.size
        out = sensory.astype(np.float32).copy()
        weights = {
            "audio_pat": 0.18,
            "taste_pat": 0.08,
            "prop_pat": 0.22,
            "vest_pat": 0.1,
            "sc_pat": 0.12,
        }
        for key, w in weights.items():
            pat = stack.get(key)
            if pat is None:
                continue
            p = np.asarray(pat, dtype=np.float32).ravel()[:n]
            if p.size < n:
                p = np.pad(p, (0, n - p.size))
            out[: p.size] = np.clip(out[: p.size] + p * w, 0, 1)
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "audition": self.audition.to_dict(),
            "gustation": self.gustation.to_dict(),
            "proprioception": self.proprioception.to_dict(),
            "vestibular": self.vestibular.to_dict(),
            "colliculus": self.colliculus.to_dict(),
            "channels": self.last_channels,
        }
