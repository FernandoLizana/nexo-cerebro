"""
Replay hipocampal diurno — micro-consolidación tras sorpresa alta (despierto).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import numpy as np

from .sleep_architecture import _fit_sensory_pattern

if TYPE_CHECKING:
    from .mind import InfantApeBrain


@dataclass
class DaytimeReplay:
    """Replay breve en vigilia cuando algo inesperado ocurre."""

    surprise_threshold: float = 0.52
    cooldown_ticks: int = 0
    last: dict[str, Any] = field(default_factory=dict)

    def maybe_replay(
        self,
        brain: InfantApeBrain,
        *,
        surprise: float,
        trigger_label: str = "",
    ) -> dict[str, Any] | None:
        if self.cooldown_ticks > 0:
            self.cooldown_ticks -= 1
            return None
        conscious_urgency = 0.0
        if getattr(brain, "consciousness", None):
            conscious_urgency = brain.consciousness.replay_urgency()
        threshold = self.surprise_threshold - conscious_urgency * 0.22
        if hasattr(brain, "memory_dynamics"):
            threshold = brain.memory_dynamics.daytime_replay_threshold(brain, threshold)
        if surprise < threshold and conscious_urgency < 0.52:
            return None
        if brain.brainstem.sleep_pressure > 0.62:
            return None
        if brain.hippocampus.size < 1:
            return None

        replay_mods = SimpleNamespace(
            acetylcholine=float(np.clip(brain.modulators.acetylcholine + 0.08, 0, 1)),
            cortisol=brain.hypothalamus.cortisol,
        )
        mem = brain.hippocampus.sample_for_replay(
            sleep_pressure=brain.brainstem.sleep_pressure * 0.5,
            modulators=replay_mods,
            sleep_phase="daytime",
        )
        if mem is None:
            return None

        raw = mem.get("pattern", mem.get("sensory"))
        if raw is None:
            sensory = np.zeros(brain.n_sensory, dtype=np.float32)
        else:
            sensory = _fit_sensory_pattern(raw, brain.n_sensory)
        steps = int(np.clip(10 + surprise * 14, 12, 28))
        brain.oscillators.force_mode("retrieve", ticks=steps)
        snap = brain._simulate(
            sensory,
            total_steps=steps,
            cortisol=brain.hypothalamus.cortisol,
        )
        brain.modulators.acetylcholine = float(
            np.clip(brain.modulators.acetylcholine + 0.03, 0, 1)
        )
        brain.modulators.dopamine = float(np.clip(brain.modulators.dopamine + 0.04, 0, 1))

        label = (mem.get("label") or trigger_label or "replay")[:50]
        self.cooldown_ticks = max(8, int(20 * (1.0 - surprise)))
        self.last = {
            "label": label,
            "surprise": round(surprise, 3),
            "conscious_urgency": round(conscious_urgency, 3),
            "steps": steps,
            "similarity": mem.get("similarity"),
            "replay_weight": mem.get("replay_weight"),
            "motor": snap.get("spikes", {}).get("motor_raw", [])[:6],
        }
        return self.last

    def to_dict(self) -> dict:
        return dict(self.last) if self.last else {}
