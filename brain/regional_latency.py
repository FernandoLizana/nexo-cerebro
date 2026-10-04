"""
Latencias inter-regionales — materia blanca como retardo (Brain Facts / tractografía).

Señales entre regiones distantes llegan con delay proporcional a la "distancia".
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np

# ms aproximados entre pares de regiones (orden de magnitud humana)
REGION_LATENCY_MS: dict[tuple[str, str], float] = {
    ("thalamus", "sensory_cortex"): 3.0,
    ("sensory_cortex", "hippocampus"): 8.0,
    ("hippocampus", "prefrontal"): 12.0,
    ("amygdala", "hypothalamus"): 4.0,
    ("prefrontal", "motor"): 6.0,
    ("motor", "cerebellum"): 5.0,
    ("cerebellum", "motor"): 5.0,
    ("insula", "salience"): 4.0,
    ("cingulate", "prefrontal"): 5.0,
    ("brainstem", "thalamus"): 2.0,
    ("hypothalamus", "pituitary"): 6.0,
    ("hippocampus", "cortex"): 15.0,
    ("default_mode", "executive"): 10.0,
    ("executive", "default_mode"): 10.0,
}

# Tractos interlobulares (materia blanca asociativa)
LOBE_LATENCY_MS: dict[tuple[str, str], float] = {
    ("occipital", "temporal"): 9.0,
    ("temporal", "parietal"): 8.0,
    ("parietal", "frontal"): 11.0,
    ("frontal", "motor"): 6.0,
    ("occipital", "parietal"): 12.0,
    ("temporal", "frontal"): 14.0,
    ("occipital", "frontal"): 18.0,
}

LOBE_WHITE_MATTER_CHAIN: tuple[tuple[str, str], ...] = (
    ("occipital", "temporal"),
    ("temporal", "parietal"),
    ("parietal", "frontal"),
    ("frontal", "motor"),
)


def latency_ms(src: str, dst: str) -> float:
    if src == dst:
        return 0.5
    if (src, dst) in LOBE_LATENCY_MS:
        return LOBE_LATENCY_MS[(src, dst)]
    if (dst, src) in LOBE_LATENCY_MS:
        return LOBE_LATENCY_MS[(dst, src)]
    return REGION_LATENCY_MS.get((src, dst), REGION_LATENCY_MS.get((dst, src), 7.0))


@dataclass
class DelayedSignal:
    src: str
    dst: str
    strength: float
    deliver_at_ms: float
    label: str = ""


@dataclass
class RegionalSignalBus:
    """Cola de señales diferidas entre módulos."""

    clock_ms: float = 0.0
    pending: deque[DelayedSignal] = field(default_factory=deque)
    delivered: list[dict[str, Any]] = field(default_factory=list)
    max_pending: int = 64

    def tick(self, dt_ms: float = 1.0) -> list[dict[str, Any]]:
        self.clock_ms += dt_ms
        out: list[dict[str, Any]] = []
        remain: deque[DelayedSignal] = deque()
        while self.pending:
            sig = self.pending.popleft()
            if sig.deliver_at_ms <= self.clock_ms:
                item = {
                    "from": sig.src,
                    "to": sig.dst,
                    "strength": round(sig.strength, 3),
                    "latency_ms": round(sig.deliver_at_ms - (self.clock_ms - dt_ms), 2),
                    "label": sig.label,
                }
                out.append(item)
                self.delivered.append(item)
            else:
                remain.append(sig)
        self.pending = remain
        if len(self.delivered) > 32:
            self.delivered = self.delivered[-32:]
        return out

    def emit(self, src: str, dst: str, strength: float, *, label: str = "") -> None:
        if strength < 0.05:
            return
        delay = latency_ms(src, dst)
        self.pending.append(
            DelayedSignal(
                src=src,
                dst=dst,
                strength=float(strength),
                deliver_at_ms=self.clock_ms + delay,
                label=label,
            )
        )
        while len(self.pending) > self.max_pending:
            self.pending.popleft()

    def apply_delivered(self, brain, delivered: list[dict[str, Any]]) -> None:
        """Refuerzo ligero en moduladores al llegar señales diferidas."""
        for d in delivered:
            s = float(d["strength"])
            dst = d["to"]
            if dst in ("prefrontal", "executive"):
                brain.modulators.acetylcholine = float(
                    np.clip(brain.modulators.acetylcholine + 0.015 * s, 0, 1)
                )
            elif dst in ("motor", "cerebellum"):
                brain.modulators.dopamine = float(np.clip(brain.modulators.dopamine + 0.012 * s, 0, 1))
            elif dst in ("amygdala", "salience"):
                brain.modulators.norepinephrine = float(
                    np.clip(brain.modulators.norepinephrine + 0.018 * s, 0, 1)
                )
            elif dst == "hippocampus":
                brain.modulators.acetylcholine = float(
                    np.clip(brain.modulators.acetylcholine + 0.01 * s, 0, 1)
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "clock_ms": round(self.clock_ms, 1),
            "pending": len(self.pending),
            "recent": self.delivered[-6:],
        }
