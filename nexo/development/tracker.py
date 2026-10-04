"""Seguimiento de etapas desarrolladoras."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DevelopmentStage(str, Enum):
    INFANT = "infant"
    JUVENILE = "juvenile"
    MATURE = "mature"


@dataclass
class DevelopmentTracker:
    """Maduración lenta por consolidación y experiencia."""

    stage: DevelopmentStage = DevelopmentStage.INFANT
    maturation: float = 0.0
    consolidations: int = 0
    wm_capacity_bonus: int = 0
    noise_reduction: float = 0.0

    def register_consolidation(self) -> None:
        self.consolidations += 1
        self.maturation = min(1.0, self.consolidations * 0.04 + self.maturation * 0.98 + 0.02)
        self._update_stage()

    def tick(self, *, simulation_tick: int) -> None:
        self.maturation = min(1.0, self.maturation + 0.0005)
        if simulation_tick % 50 == 0 and simulation_tick > 0:
            self._update_stage()

    def _update_stage(self) -> None:
        if self.maturation >= 0.65:
            self.stage = DevelopmentStage.MATURE
            self.wm_capacity_bonus = 1
            self.noise_reduction = 0.15
        elif self.maturation >= 0.25:
            self.stage = DevelopmentStage.JUVENILE
            self.wm_capacity_bonus = 0
            self.noise_reduction = 0.08
        else:
            self.stage = DevelopmentStage.INFANT
            self.wm_capacity_bonus = 0
            self.noise_reduction = 0.0

    def to_dict(self) -> dict[str, str | float | int]:
        return {
            "stage": self.stage.value,
            "maturation": round(self.maturation, 4),
            "consolidations": self.consolidations,
            "wm_capacity_bonus": self.wm_capacity_bonus,
            "noise_reduction": self.noise_reduction,
        }
