"""
Ciclo vital: edad, vitalidad, reproducción, hijo, muerte.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import random


@dataclass
class LifecycleState:
    age_ticks: int = 0
    vitality: float = 1.0
    stage: str = "joven"
    alive: bool = True
    generation: int = 1
    parent_name: str | None = None
    mate_bond: float = 0.0
    offspring: dict | None = None
    death_cause: str | None = None
    ticks_per_year: int = 180
    max_age_years: float = 75.0
    mature_age_years: float = 16.0
    fertile_until_years: float = 45.0
    reproduce_bond_threshold: float = 0.72
    _child_names: tuple[str, ...] = ("Kai", "Luna", "Sol", "Río", "Ara", "Noa")

    @property
    def age_years(self) -> float:
        return self.age_ticks / max(self.ticks_per_year, 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "age_ticks": self.age_ticks,
            "age_years": round(self.age_years, 2),
            "vitality": round(self.vitality, 3),
            "stage": self.stage,
            "alive": self.alive,
            "generation": self.generation,
            "parent_name": self.parent_name,
            "mate_bond": round(self.mate_bond, 3),
            "offspring": self.offspring,
            "death_cause": self.death_cause,
            "can_reproduce": self.can_reproduce(),
            "neuro": self.neuro_modulation(),
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> LifecycleState:
        if not data:
            return cls()
        lc = cls()
        lc.age_ticks = int(data.get("age_ticks", 0))
        lc.vitality = float(data.get("vitality", 1.0))
        lc.stage = str(data.get("stage", "joven"))
        lc.alive = bool(data.get("alive", True))
        lc.generation = int(data.get("generation", 1))
        lc.parent_name = data.get("parent_name")
        lc.mate_bond = float(data.get("mate_bond", 0))
        lc.offspring = data.get("offspring")
        lc.death_cause = data.get("death_cause")
        return lc

    def _update_stage(self) -> None:
        y = self.age_years
        if y < 3:
            self.stage = "infante"
        elif y < 12:
            self.stage = "nino"
        elif y < self.mature_age_years:
            self.stage = "adolescente"
        elif y < 55:
            self.stage = "adulto"
        else:
            self.stage = "anciano"

    def neuro_modulation(self) -> dict[str, float]:
        """
        Escalas por etapa vital (sobre el perfil base).
        No eligen acciones: solo plasticidad / inhibición PFC.
        """
        table = {
            "infante": {"plasticity_scale": 1.55, "pfc_inhibition_scale": 0.62, "prune_rate": 0.0},
            "nino": {"plasticity_scale": 1.28, "pfc_inhibition_scale": 0.78, "prune_rate": 0.004},
            "adolescente": {"plasticity_scale": 1.22, "pfc_inhibition_scale": 0.72, "prune_rate": 0.002},
            "joven": {"plasticity_scale": 1.15, "pfc_inhibition_scale": 0.88, "prune_rate": 0.0},
            "adulto": {"plasticity_scale": 0.92, "pfc_inhibition_scale": 1.08, "prune_rate": 0.012},
            "anciano": {"plasticity_scale": 0.68, "pfc_inhibition_scale": 0.95, "prune_rate": 0.018},
        }
        return dict(table.get(self.stage, table.get("joven", table["adulto"])))

    def epigenetic_profile(self) -> dict[str, float]:
        """
        Capa epigenética por etapa — metilación silencia plasticidad en adulto/anciano.
        No elige acciones: modula plasticity_mult / poda sináptica.
        """
        base = self.neuro_modulation()
        methylation = {
            "infante": 0.12,
            "nino": 0.18,
            "adolescente": 0.22,
            "joven": 0.28,
            "adulto": 0.46,
            "anciano": 0.64,
        }.get(self.stage, 0.3)
        expression = base["plasticity_scale"] * (1.0 - 0.32 * methylation)
        return {
            **base,
            "methylation": methylation,
            "expression_plasticity": round(expression, 3),
            "epigenetic_prune_rate": base.get("prune_rate", 0.0) + methylation * 0.008,
        }

    def can_reproduce(self) -> bool:
        if not self.alive or self.offspring:
            return False
        y = self.age_years
        return self.mature_age_years <= y <= self.fertile_until_years and self.vitality > 0.35

    def tick(
        self,
        *,
        body: Any,
        companion_bond: float,
        attachment: float,
        oxytocin: float,
        comfort: float,
    ) -> list[dict]:
        """Un paso de edad/vitalidad. Devuelve eventos del ciclo vital."""
        if not self.alive:
            return []

        self.age_ticks += 1
        self._update_stage()
        events: list[dict] = []

        self.mate_bond = min(
            1.0,
            0.65 * companion_bond + 0.25 * attachment + 0.1 * oxytocin,
        )

        age_wear = max(0.0, (self.age_years - 40) * 0.00008)
        neglect = max(0.0, 0.45 - comfort) * 0.002
        self.vitality = max(0.0, min(1.0, self.vitality - age_wear - neglect + 0.0004))

        if self.age_years >= self.max_age_years:
            self.alive = False
            self.death_cause = "vejez"
            events.append({"type": "lifecycle_death", "cause": "vejez"})
        elif self.vitality <= 0.02:
            self.alive = False
            self.death_cause = "agotamiento"
            events.append({"type": "lifecycle_death", "cause": "agotamiento"})

        if self.can_reproduce() and self.mate_bond >= self.reproduce_bond_threshold:
            if self.age_ticks % 90 == 0:
                events.append({"type": "lifecycle_fertile", "bond": round(self.mate_bond, 2)})

        return events

    def reproduce(
        self,
        *,
        nexo_name: str,
        companion_name: str,
        nexo_x: float,
        nexo_y: float,
    ) -> dict:
        if not self.can_reproduce():
            return {"ok": False, "reason": "no_fertile"}
        if self.mate_bond < self.reproduce_bond_threshold:
            return {"ok": False, "reason": "bond_low", "bond": self.mate_bond}

        child_name = random.choice(self._child_names)
        self.offspring = {
            "name": child_name,
            "generation": self.generation + 1,
            "parents": [nexo_name, companion_name],
            "born_age_ticks": self.age_ticks,
            "x": nexo_x + random.uniform(-20, 20),
            "y": nexo_y + random.uniform(-15, 15),
        }
        self.vitality = max(0.15, self.vitality - 0.12)
        return {"ok": True, "offspring": dict(self.offspring)}

    def apply_deep_transformation(self) -> dict:
        """Transformación profunda: baja la vitalidad, no cierra el ciclo."""
        self.vitality = max(0.08, self.vitality - 0.18)
        return {"transformed": True, "vitality": self.vitality}
