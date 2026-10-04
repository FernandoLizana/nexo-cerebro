"""Resultados de tareas conductuales integradas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IntegratedTaskResult:
    task_id: str
    ablation_id: str
    seed: int
    primary_metrics: dict[str, float]
    secondary_metrics: dict[str, float] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "ablation_id": self.ablation_id,
            "seed": self.seed,
            "primary_metrics": self.primary_metrics,
            "secondary_metrics": self.secondary_metrics,
            "details": self.details,
        }
