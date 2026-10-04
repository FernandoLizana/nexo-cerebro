"""Núcleo reticular talámico — inhibición selectiva."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReticularNucleus:
    """Suprime modalidades de baja relevancia o alta habituación."""

    inhibition_strength: float = 0.6
    _habituation: dict[str, float] = field(default_factory=dict)

    def update_habituation(self, modality: str, surprise: float) -> None:
        prev = self._habituation.get(modality, 0.0)
        self._habituation[modality] = prev * 0.9 + surprise * 0.08

    def mask(self, modalities: list[str], *, goals: tuple[str, ...]) -> dict[str, float]:
        masks: dict[str, float] = {}
        for m in modalities:
            hab = self._habituation.get(m, 0.0)
            gain = 1.0 - self.inhibition_strength * min(0.9, hab)
            if m == "food" and "eat" in goals:
                gain = min(1.0, gain + 0.25)
            if m == "danger" and ("avoid_harm" in goals or "survive" in goals):
                gain = min(1.0, gain + 0.35)
            if m == "distractor" and "eat" in goals:
                gain = max(0.2, gain - 0.15)
            masks[m] = max(0.1, min(1.0, gain))
        return masks
