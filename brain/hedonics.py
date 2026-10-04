"""
Circuito hedónico — placer, satisfacción, cansancio sentido, vía dopamina/μ-opioide/endocannabinoide.

Integra cuerpo, biomecánica, afecto y experiencias (comida, cosecha, confort, vínculo).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .mind import InfantApeBrain


@dataclass
class HedonicState:
    """Estado hedónico continuo (no binario)."""

    pleasure: float = 0.35
    satisfaction: float = 0.5
    craving: float = 0.0
    satiety: float = 0.0
    mu_opioid: float = 0.38
    endocannabinoid: float = 0.32
    fatigue_felt: float = 0.0
    last_reward: str = ""
    _log: list[str] = field(default_factory=list)

    def reward(
        self,
        kind: str,
        intensity: float,
        *,
        label: str = "",
        affect=None,
    ) -> None:
        """Experiencia hedónica puntual → química."""
        amount = float(np.clip(intensity, 0, 1))
        self.last_reward = label or kind

        if kind in ("eat_cooked", "cook", "meal"):
            self.satiety = float(np.clip(self.satiety + amount * 0.55, 0, 1))
            self.craving = float(np.clip(self.craving - amount * 0.45, 0, 1))
            self.mu_opioid = float(np.clip(self.mu_opioid + amount * 0.25, 0, 1))
            self.endocannabinoid = float(np.clip(self.endocannabinoid + amount * 0.18, 0, 1))
            self.satisfaction = float(np.clip(self.satisfaction + amount * 0.35, 0, 1))
            self._log_reward(f"μ-opioide↑ comida ({label or kind})")
            if affect:
                affect.process_stimulus(
                    valence=0.45 + amount * 0.35,
                    arousal=0.35,
                    novelty=0.2,
                    pain=0.0,
                    social_bond=0.05,
                    attention=0.4,
                )
        elif kind == "harvest":
            self.satisfaction = float(np.clip(self.satisfaction + amount * 0.28, 0, 1))
            self.endocannabinoid = float(np.clip(self.endocannabinoid + amount * 0.12, 0, 1))
            self._log_reward(f"satisfacción↑ cosecha ({label})")
            if affect:
                affect.process_stimulus(valence=0.28, arousal=0.42, novelty=0.35, attention=0.5)
        elif kind == "eat_raw":
            self.satiety = float(np.clip(self.satiety + amount * 0.35, 0, 1))
            self.craving = float(np.clip(self.craving - amount * 0.25, 0, 1))
            self._log_reward("comida cruda — placer moderado")
            if affect:
                affect.process_stimulus(valence=0.12, arousal=0.3, novelty=0.15)
        elif kind == "comfort":
            self.endocannabinoid = float(np.clip(self.endocannabinoid + amount * 0.22, 0, 1))
            self.mu_opioid = float(np.clip(self.mu_opioid + amount * 0.08, 0, 1))
            if affect:
                affect.process_stimulus(valence=0.25, arousal=0.2, novelty=0.05, social_bond=0.1)
        elif kind == "social":
            self.mu_opioid = float(np.clip(self.mu_opioid + amount * 0.15, 0, 1))
            if affect:
                affect.process_stimulus(valence=0.35, arousal=0.4, novelty=0.18, social_bond=amount)
        elif kind == "pain_relief":
            self.mu_opioid = float(np.clip(self.mu_opioid + amount * 0.2, 0, 1))
            self.pleasure = float(np.clip(self.pleasure + amount * 0.15, 0, 1))

        self._recompute_pleasure()

    def tick(self, brain: InfantApeBrain) -> None:
        body = brain.body
        bio = brain.biomech

        self.craving = float(np.clip(body.hunger * 0.85 + (1 - self.satiety) * 0.15, 0, 1))
        self.fatigue_felt = float(np.clip(
            body.fatigue * 0.55 + bio.physical_fatigue * 0.45,
            0, 1,
        ))
        self.satiety = float(np.clip(self.satiety - 0.004 - body.hunger * 0.002, 0, 1))

        if body.comfort > 0.65:
            self.endocannabinoid = float(np.clip(self.endocannabinoid + 0.008, 0, 1))
        if body.total_pain() > 0.2:
            self.mu_opioid = float(np.clip(self.mu_opioid - body.total_pain() * 0.02, 0, 1))

        for pool, rate in (
            ("mu_opioid", 0.04),
            ("endocannabinoid", 0.035),
        ):
            cur = getattr(self, pool)
            setattr(self, pool, float(np.clip(cur * (1 - rate) + 0.02, 0, 1)))

        self._recompute_pleasure()
        body.pleasure = self.pleasure
        body.satiety = self.satiety

    def _recompute_pleasure(self) -> None:
        base = (
            0.28 * self.mu_opioid
            + 0.22 * self.endocannabinoid
            + 0.18 * self.satisfaction
            + 0.12 * self.satiety
        )
        self.pleasure = float(np.clip(
            base - self.fatigue_felt * 0.35 - self.craving * 0.2,
            0, 1,
        ))

    def feelings(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        if self.pleasure > 0.15:
            out.append({"signal": "placer", "intensity": round(self.pleasure, 3)})
        if self.satisfaction > 0.2:
            out.append({"signal": "satisfacción", "intensity": round(self.satisfaction, 3)})
        if self.craving > 0.25:
            out.append({"signal": "antojo", "intensity": round(self.craving, 3)})
        if self.satiety > 0.35:
            out.append({"signal": "saciedad", "intensity": round(self.satiety, 3)})
        if self.fatigue_felt > 0.35:
            out.append({"signal": "cansancio profundo", "intensity": round(self.fatigue_felt, 3)})
        if self.mu_opioid > 0.55:
            out.append({"signal": "bienestar", "intensity": round(self.mu_opioid, 3)})
        if self.endocannabinoid > 0.5:
            out.append({"signal": "relajación", "intensity": round(self.endocannabinoid, 3)})
        out.sort(key=lambda x: -x["intensity"])
        return out[:8]

    def drives(self) -> dict[str, float]:
        return {
            "seek_cook": float(np.clip(self.craving * 0.5, 0, 1)),
            "seek_pleasure": float(np.clip(0.45 - self.pleasure + self.craving * 0.3, 0, 1)),
        }

    def _log_reward(self, msg: str) -> None:
        self._log.insert(0, msg)
        self._log = self._log[:6]

    def to_dict(self) -> dict[str, Any]:
        return {
            "pleasure": round(self.pleasure, 3),
            "satisfaction": round(self.satisfaction, 3),
            "craving": round(self.craving, 3),
            "satiety": round(self.satiety, 3),
            "mu_opioid": round(self.mu_opioid, 3),
            "endocannabinoid": round(self.endocannabinoid, 3),
            "fatigue_felt": round(self.fatigue_felt, 3),
            "feelings": self.feelings(),
            "last_reward": self.last_reward,
            "log": self._log[:4],
            "wanting_note": "DA-driven motivation; liking = mu-opioid pleasure",
        }

    def load_dict(self, d: dict | None) -> None:
        if not d:
            return
        for k in (
            "pleasure", "satisfaction", "craving", "satiety",
            "mu_opioid", "endocannabinoid", "fatigue_felt",
        ):
            if k in d:
                setattr(self, k, float(d[k]))
