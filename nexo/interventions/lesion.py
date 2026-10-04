"""Lesiones virtuales fine-grained sobre aristas del conectoma."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LesionState:
    """Estado mutable de lesiones aplicadas al router."""

    severed: set[tuple[str, str]] = field(default_factory=set)
    weight_scale: dict[tuple[str, str], float] = field(default_factory=dict)
    latency_add: dict[tuple[str, str], int] = field(default_factory=dict)

    def is_severed(self, source: str, target: str) -> bool:
        return (source, target) in self.severed

    def scale_for(self, source: str, target: str) -> float:
        if self.is_severed(source, target):
            return 0.0
        return self.weight_scale.get((source, target), 1.0)

    def effective_latency(self, source: str, target: str, base: int) -> int:
        return base + self.latency_add.get((source, target), 0)

    def sever(self, source: str, target: str) -> None:
        self.severed.add((source, target))

    def set_weight_scale(self, source: str, target: str, scale: float) -> None:
        self.weight_scale[(source, target)] = scale

    def add_latency(self, source: str, target: str, extra_ticks: int) -> None:
        self.latency_add[(source, target)] = extra_ticks

    def active_lesions(self) -> list[dict[str, str | float | int]]:
        out: list[dict[str, str | float | int]] = []
        for source, target in sorted(self.severed):
            out.append({"source": source, "target": target, "kind": "sever"})
        for (source, target), scale in sorted(self.weight_scale.items()):
            if (source, target) not in self.severed:
                out.append({"source": source, "target": target, "kind": "weight_scale", "scale": scale})
        for (source, target), extra in sorted(self.latency_add.items()):
            out.append({"source": source, "target": target, "kind": "latency_add", "extra_ticks": extra})
        return out


@dataclass(frozen=True)
class LesionSpec:
    """Especificación declarativa de una lesión connectome."""

    lesion_id: str
    label: str
    sever: tuple[tuple[str, str], ...] = ()
    weight_scale: tuple[tuple[str, str, float], ...] = ()
    latency_add: tuple[tuple[str, str, int], ...] = ()

    def apply_to(self, state: LesionState) -> LesionState:
        for source, target in self.sever:
            state.sever(source, target)
        for source, target, scale in self.weight_scale:
            state.set_weight_scale(source, target, scale)
        for source, target, extra in self.latency_add:
            state.add_latency(source, target, extra)
        return state
