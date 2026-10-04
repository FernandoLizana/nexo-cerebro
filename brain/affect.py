"""
Química emocional — dinámica sináptica simplificada.

Modela liberación → unión a receptor → recaptación con cinéticas distintas
( rápida: dopamina; lenta: cortisol vía eje HPA ).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class SynapticPool:
    """Un neurotransmisor / hormona con pool sináptico y ocupación receptora."""

    name: str
    synaptic: float = 0.0
    bound: float = 0.45
    baseline: float = 0.45
    reuptake: float = 0.18
    binding: float = 0.42
    half_life_ticks: int = 6

    def release(self, amount: float) -> None:
        self.synaptic = float(np.clip(self.synaptic + max(0.0, amount), 0, 1.5))

    def step(self) -> None:
        uptake = self.reuptake * (0.55 + 0.45 / max(self.half_life_ticks, 1))
        bind_rate = self.binding * self.synaptic * (1.0 - self.bound)
        unbind = uptake * 0.35 * self.bound
        self.bound = float(np.clip(self.bound + bind_rate - unbind, 0, 1))
        self.synaptic = float(np.clip(self.synaptic * (1.0 - uptake) + self.baseline * 0.02, 0, 1.2))
        self.bound = float(np.clip(0.92 * self.bound + 0.08 * self.baseline, 0, 1))


@dataclass
class AffectChemistry:
    """
    Estado químico subjetivo: VTA, rafe, locus coeruleus, PVN (cortisol), etc.
    """

    dopamine: SynapticPool = field(default_factory=lambda: SynapticPool("dopamina", baseline=0.52, reuptake=0.28, half_life_ticks=4))
    serotonin: SynapticPool = field(default_factory=lambda: SynapticPool("serotonina", baseline=0.55, reuptake=0.12, half_life_ticks=10))
    norepinephrine: SynapticPool = field(default_factory=lambda: SynapticPool("noradrenalina", baseline=0.45, reuptake=0.22, half_life_ticks=5))
    acetylcholine: SynapticPool = field(default_factory=lambda: SynapticPool("acetilcolina", baseline=0.5, reuptake=0.2, half_life_ticks=6))
    gaba: SynapticPool = field(default_factory=lambda: SynapticPool("GABA", baseline=0.4, reuptake=0.15, half_life_ticks=8))
    glutamate: SynapticPool = field(default_factory=lambda: SynapticPool("glutamato", baseline=0.55, reuptake=0.2, half_life_ticks=5))
    oxytocin: SynapticPool = field(default_factory=lambda: SynapticPool("oxitocina", baseline=0.42, reuptake=0.1, half_life_ticks=12))
    cortisol: SynapticPool = field(default_factory=lambda: SynapticPool("cortisol", baseline=0.22, reuptake=0.06, half_life_ticks=24))

    _hpa_stress: float = field(default=0.0, init=False)
    _last_felt: str = field(default="calma", init=False)
    _process_log: list[str] = field(default_factory=list, init=False)

    def process_stimulus(
        self,
        *,
        valence: float,
        arousal: float,
        novelty: float,
        pain: float = 0.0,
        social_bond: float = 0.0,
        attention: float = 0.5,
        surprise: float = 0.0,
    ) -> None:
        """Liberación sináptica tras estímulo (amígdala + cuerpo + vínculo)."""
        v, a = float(valence), float(arousal)
        threat = a * max(-v, 0.0)
        reward = max(v, 0.0) * (0.5 + novelty * 0.5) + surprise * 0.35

        self.dopamine.release(0.08 + reward * 0.35 + novelty * 0.2)
        self.serotonin.release(0.04 + max(v, 0) * 0.12 - threat * 0.18 - pain * 0.1)
        self.norepinephrine.release(0.06 + a * 0.28 + threat * 0.25 + pain * 0.15)
        self.acetylcholine.release(0.05 + attention * 0.22 + novelty * 0.15)
        self.glutamate.release(0.07 + a * 0.2 + surprise * 0.2)
        self.gaba.release(0.03 + (0.15 if a > 0.65 else 0) + (0.1 if pain > 0.2 else 0))
        self.oxytocin.release(0.04 + social_bond * 0.3 + max(v, 0) * 0.12)

        self._hpa_stress = float(np.clip(0.7 * self._hpa_stress + 0.3 * (threat + pain * 0.6), 0, 1))
        self.cortisol.release(0.02 + self._hpa_stress * 0.12)

        if threat > 0.35:
            self._process_log.insert(0, f"amígdala → NE↑ amenaza ({threat:.0%})")
        if reward > 0.25:
            self._process_log.insert(0, f"VTA → DA↑ recompensa ({reward:.0%})")
        if social_bond > 0.3:
            self._process_log.insert(0, f"hipófisis → OT↑ vínculo")
        self._process_log = self._process_log[:6]

    def step(self) -> dict:
        """Recaptación, unión receptora y retroalimentación cruzada."""
        if self.cortisol.bound > 0.55:
            self.serotonin.release(-0.04)
        if self.dopamine.bound > 0.7:
            self.gaba.release(0.03)
        if self.norepinephrine.bound > 0.65 and self.gaba.bound > 0.45:
            self.norepinephrine.synaptic *= 0.92

        for pool in (
            self.dopamine,
            self.serotonin,
            self.norepinephrine,
            self.acetylcholine,
            self.gaba,
            self.glutamate,
            self.oxytocin,
            self.cortisol,
        ):
            pool.step()

        self._hpa_stress *= 0.96
        self._last_felt = self._compute_felt()
        return self.to_dict()

    def tick_decay(self) -> None:
        """Paso basal entre estímulos (homeostasis lenta)."""
        self.step()

    def sync_modulators(self, mods) -> None:
        """Mezcla ocupación receptora en neuromoduladores globales."""
        blend = 0.38
        mods.dopamine = float(np.clip((1 - blend) * mods.dopamine + blend * self.dopamine.bound, 0, 1))
        mods.serotonin = float(np.clip((1 - blend) * mods.serotonin + blend * self.serotonin.bound, 0, 1))
        mods.norepinephrine = float(
            np.clip((1 - blend) * mods.norepinephrine + blend * self.norepinephrine.bound, 0, 1)
        )
        mods.acetylcholine = float(
            np.clip((1 - blend) * mods.acetylcholine + blend * self.acetylcholine.bound, 0, 1)
        )
        mods.gaba_tone = float(np.clip((1 - blend) * mods.gaba_tone + blend * self.gaba.bound, 0, 1))
        mods.glutamate_drive = float(
            np.clip((1 - blend) * mods.glutamate_drive + blend * self.glutamate.bound, 0, 1)
        )
        mods.oxytocin = float(np.clip((1 - blend) * mods.oxytocin + blend * self.oxytocin.bound, 0, 1))

    def sync_hypothalamus(self, hypo, *, valence: float, arousal: float) -> None:
        hypo.dopamine = float(np.clip(0.6 * hypo.dopamine + 0.4 * self.dopamine.bound, 0, 1))
        hypo.cortisol = float(np.clip(0.55 * hypo.cortisol + 0.45 * self.cortisol.bound, 0, 1))
        hypo.oxytocin = float(np.clip(0.65 * hypo.oxytocin + 0.35 * self.oxytocin.bound, 0, 1))

    def subjective_valence(self) -> float:
        return float(
            np.clip(
                0.35 * self.dopamine.bound
                + 0.25 * self.serotonin.bound
                + 0.2 * self.oxytocin.bound
                - 0.35 * self.cortisol.bound
                - 0.2 * self.norepinephrine.bound * max(-1, 0),
                -1,
                1,
            )
        )

    def subjective_arousal(self) -> float:
        return float(
            np.clip(
                0.4 * self.norepinephrine.bound
                + 0.3 * self.glutamate.bound
                + 0.2 * self.dopamine.bound
                - 0.25 * self.gaba.bound,
                0,
                1,
            )
        )

    def _compute_felt(self) -> str:
        da, se, ne, ot, cor, gaba = (
            self.dopamine.bound,
            self.serotonin.bound,
            self.norepinephrine.bound,
            self.oxytocin.bound,
            self.cortisol.bound,
            self.gaba.bound,
        )
        if cor > 0.62 and ne > 0.55:
            return "angustia"
        if ne > 0.62 and da < 0.45:
            return "miedo"
        if da > 0.62 and se > 0.5:
            return "euforia"
        if da > 0.55 and ot > 0.5:
            return "afecto"
        if ot > 0.58:
            return "ternura"
        if se > 0.58 and gaba > 0.45:
            return "serenidad"
        if da > 0.5 and ne > 0.45:
            return "curiosidad"
        if cor > 0.55:
            return "tensión"
        if se < 0.38 and ne > 0.5:
            return "inquietud"
        if gaba > 0.55:
            return "calma"
        return "neutralidad"

    def pool_dict(self, pool: SynapticPool) -> dict:
        return {
            "synaptic": round(pool.synaptic, 3),
            "bound": round(pool.bound, 3),
            "baseline": round(pool.baseline, 3),
        }

    def to_dict(self) -> dict:
        return {
            "felt": self._last_felt,
            "valence": round(self.subjective_valence(), 3),
            "arousal": round(self.subjective_arousal(), 3),
            "pools": {
                "dopamine": self.pool_dict(self.dopamine),
                "serotonin": self.pool_dict(self.serotonin),
                "norepinephrine": self.pool_dict(self.norepinephrine),
                "acetylcholine": self.pool_dict(self.acetylcholine),
                "gaba": self.pool_dict(self.gaba),
                "glutamate": self.pool_dict(self.glutamate),
                "oxytocin": self.pool_dict(self.oxytocin),
                "cortisol": self.pool_dict(self.cortisol),
            },
            "hpa_stress": round(self._hpa_stress, 3),
            "process_log": self._process_log[:4],
        }
