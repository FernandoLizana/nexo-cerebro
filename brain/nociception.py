"""
Terminal nociceptivo somático — vía Aδ (rápida) y C (lenta) → asta dorsal → tálamo → ínsula.

No asigna «dolor» como variable mágica: transduce estímulos periféricos (mecánico, térmico,
isquémico, químico) en señales que el cuerpo integra como malestar real.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class NociceptiveTerminal:
    """Terminal periférico + relé medular simplificado."""

    a_delta: dict[str, float] = field(default_factory=lambda: {
        "head": 0.0, "torso": 0.0, "limbs": 0.0,
    })
    c_fiber: dict[str, float] = field(default_factory=lambda: {
        "head": 0.0, "torso": 0.0, "limbs": 0.0, "viscera": 0.0,
    })
    dorsal_horn: dict[str, float] = field(default_factory=lambda: {
        "lamina_I": 0.0, "lamina_II": 0.0, "wide_dynamic": 0.0,
    })
    thalamic_relay: float = 0.0
    central_sensitization: float = 0.0
    last_stimuli: list[dict[str, Any]] = field(default_factory=list)

    A_DECAY = 0.72
    C_DECAY = 0.94
    DORSAL_DECAY = 0.88

    def transduce(
        self,
        *,
        region: str,
        modality: str,
        intensity: float,
        label: str = "",
    ) -> None:
        """Estímulo periférico → fibras Aδ/C."""
        amount = float(np.clip(intensity, 0, 1))
        if amount < 0.01:
            return
        reg = self._norm_region(region)
        entry = {"region": reg, "modality": modality, "intensity": round(amount, 3), "label": label[:60]}
        self.last_stimuli.insert(0, entry)
        self.last_stimuli = self.last_stimuli[:12]

        if modality in ("mechanical", "sharp", "collision"):
            self.a_delta[reg] = float(np.clip(self.a_delta.get(reg, 0) + amount * 0.85, 0, 1))
            self.c_fiber[reg] = float(np.clip(self.c_fiber.get(reg, 0) + amount * 0.25, 0, 1))
        elif modality in ("thermal", "cold", "heat"):
            self.c_fiber[reg] = float(np.clip(self.c_fiber.get(reg, 0) + amount * 0.7, 0, 1))
            self.a_delta[reg] = float(np.clip(self.a_delta.get(reg, 0) + amount * 0.35, 0, 1))
        elif modality in ("ischemic", "hunger", "visceral"):
            self.c_fiber["viscera"] = float(np.clip(self.c_fiber.get("viscera", 0) + amount * 0.65, 0, 1))
            self.c_fiber["torso"] = float(np.clip(self.c_fiber.get("torso", 0) + amount * 0.4, 0, 1))
        else:
            self.c_fiber[reg] = float(np.clip(self.c_fiber.get(reg, 0) + amount * 0.55, 0, 1))

    def tick(
        self,
        body,
        *,
        room_temp: float,
        strain: float = 1.0,
        ordeal_active: bool = False,
    ) -> None:
        """Estímulos interoceptivos continuos + decaimiento + relé medular."""
        for k in self.a_delta:
            self.a_delta[k] *= self.A_DECAY
        for k in self.c_fiber:
            self.c_fiber[k] *= self.C_DECAY

        cold = max(0.0, 0.42 - room_temp)
        if cold > 0.08:
            self.transduce(region="limbs", modality="cold", intensity=cold * 0.5 * strain, label="frío periférico")
        heat = max(0.0, room_temp - 0.78)
        if heat > 0.06:
            self.transduce(region="limbs", modality="heat", intensity=heat * 0.45, label="calor periférico")

        if body.hunger > 0.78:
            self.transduce(region="torso", modality="hunger", intensity=(body.hunger - 0.75) * 1.2, label="hambre visceral")
        if body.fatigue > 0.82:
            self.transduce(region="head", modality="ischemic", intensity=(body.fatigue - 0.8) * 0.8, label="fatiga cerebral")
        if body.bladder > 0.75:
            self.transduce(region="torso", modality="visceral", intensity=(body.bladder - 0.72) * 0.9, label="distensión")
        if ordeal_active:
            self.transduce(region="torso", modality="mechanical", intensity=0.12 * strain, label="prueba heroica")

        self._relay_dorsal()
        self._project_to_body(body)

    def _relay_dorsal(self) -> None:
        a_sum = sum(self.a_delta.values())
        c_sum = sum(self.c_fiber.values())
        self.dorsal_horn["lamina_I"] = float(np.clip(a_sum * 0.55 + c_sum * 0.35, 0, 1))
        self.dorsal_horn["lamina_II"] = float(np.clip(c_sum * 0.7, 0, 1))
        windup = min(1.0, c_sum * 0.4 + a_sum * 0.2)
        self.central_sensitization = float(np.clip(self.central_sensitization * 0.92 + windup * 0.08, 0, 0.65))
        wdf = float(np.clip(a_sum * 0.45 + c_sum * 0.55 + self.central_sensitization * 0.25, 0, 1))
        self.dorsal_horn["wide_dynamic"] = wdf
        self.thalamic_relay = float(np.clip(wdf * 0.85 + self.dorsal_horn["lamina_I"] * 0.2, 0, 1))
        for k in self.dorsal_horn:
            self.dorsal_horn[k] *= self.DORSAL_DECAY
            self.dorsal_horn[k] = float(np.clip(
                self.dorsal_horn[k] + (a_sum * 0.15 if k == "lamina_I" else c_sum * 0.12),
                0, 1,
            ))

    def _project_to_body(self, body) -> None:
        sens = 1.0 + self.central_sensitization * 0.35
        body.pain_head = float(np.clip(
            self.a_delta.get("head", 0) * 0.7 + self.c_fiber.get("head", 0) * 0.55, 0, 1,
        )) * sens
        body.pain_limbs = float(np.clip(
            self.a_delta.get("limbs", 0) * 0.75 + self.c_fiber.get("limbs", 0) * 0.6, 0, 1,
        )) * sens
        body.pain_torso = float(np.clip(
            self.a_delta.get("torso", 0) * 0.65
            + self.c_fiber.get("torso", 0) * 0.7
            + self.c_fiber.get("viscera", 0) * 0.5,
            0, 1,
        )) * sens
        body.pain_ache = float(np.clip(
            self.c_fiber.get("viscera", 0) * 0.55
            + self.dorsal_horn.get("wide_dynamic", 0) * 0.35
            + self.c_fiber.get("torso", 0) * 0.25,
            0, 1,
        )) * sens

    def apply_collision(self, region: str, amount: float, *, label: str = "") -> None:
        self.transduce(region=region, modality="mechanical", intensity=amount, label=label or "golpe")

    def apply_referred_pain(self, body) -> None:
        """Dolor viscero-somático referido — vísceras → hombros/extremidades."""
        viscera = float(self.c_fiber.get("viscera", 0))
        torso = float(self.c_fiber.get("torso", 0))
        if viscera < 0.35 and torso < 0.4:
            return
        ref = float(np.clip(viscera * 0.42 + max(0.0, torso - 0.35) * 0.28, 0, 0.55))
        self.c_fiber["limbs"] = float(np.clip(self.c_fiber.get("limbs", 0) + ref * 0.35, 0, 1))
        self.a_delta["head"] = float(np.clip(self.a_delta.get("head", 0) + ref * 0.12, 0, 1))
        body.pain_limbs = float(np.clip(body.pain_limbs + ref * 0.18, 0, 1))
        body.pain_ache = float(np.clip(body.pain_ache + ref * 0.22, 0, 1))

    def gate_inhibition(
        self,
        amount: float = 0.15,
        *,
        regions: tuple[str, ...] = ("limbs", "torso", "head"),
    ) -> None:
        """Inhibición en asta dorsal — baño, reposo, contacto reconfortante."""
        f = float(np.clip(amount, 0, 0.5))
        for reg in regions:
            if reg in self.a_delta:
                self.a_delta[reg] *= 1.0 - f * 0.85
            if reg in self.c_fiber:
                self.c_fiber[reg] *= 1.0 - f * 0.75
        self.c_fiber["viscera"] = float(np.clip(self.c_fiber.get("viscera", 0) * (1 - f * 0.5), 0, 1))
        self.central_sensitization = float(np.clip(self.central_sensitization * (1 - f * 0.4), 0, 0.65))
        for k in self.dorsal_horn:
            self.dorsal_horn[k] *= 1.0 - f * 0.35

    def encode(self, n: int) -> np.ndarray:
        vec = np.zeros(min(n, 16), dtype=np.float32)
        slots = [
            sum(self.a_delta.values()),
            sum(self.c_fiber.values()),
            self.dorsal_horn.get("lamina_I", 0),
            self.dorsal_horn.get("lamina_II", 0),
            self.dorsal_horn.get("wide_dynamic", 0),
            self.thalamic_relay,
            self.central_sensitization,
            self.a_delta.get("limbs", 0),
            self.c_fiber.get("viscera", 0),
        ]
        for i, v in enumerate(slots):
            if i < vec.size:
                vec[i] = float(v)
        m = float(vec.max())
        if m > 1e-6:
            vec /= m
        return vec

    def to_dict(self) -> dict[str, Any]:
        return {
            "a_delta": {k: round(v, 3) for k, v in self.a_delta.items()},
            "c_fiber": {k: round(v, 3) for k, v in self.c_fiber.items()},
            "dorsal_horn": {k: round(v, 3) for k, v in self.dorsal_horn.items()},
            "thalamic_relay": round(self.thalamic_relay, 3),
            "central_sensitization": round(self.central_sensitization, 3),
            "last_stimuli": self.last_stimuli[:4],
            "total": round(self.total(), 3),
        }

    def total(self) -> float:
        return float(np.clip(
            sum(self.a_delta.values()) * 0.35
            + sum(self.c_fiber.values()) * 0.45
            + self.thalamic_relay * 0.25,
            0, 1,
        ))

    @staticmethod
    def _norm_region(region: str) -> str:
        r = (region or "torso").lower()
        if r in ("head", "cabeza"):
            return "head"
        if r in ("limbs", "extremidades", "limb"):
            return "limbs"
        return "torso"
