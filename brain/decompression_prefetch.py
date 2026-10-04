"""
Prefetch predictivo — calienta chunks scaffold y ensambles virtuales para el próximo tick.

Usa presupuesto separado del gobernador (no compite con recall activo).
Prioriza candidatos de deliberación PFC y objetivos en la pila de metas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

from .episodic_context import fuse_episodic_pattern
from .experiment_flags import get_flags

if TYPE_CHECKING:
    from .mind import InfantApeBrain


@dataclass
class DecompressionPrefetcher:
    last_plan: list[str] = field(default_factory=list)
    last_regions: list[str] = field(default_factory=list)
    chunks_warmed: int = 0
    assemblies_warmed: int = 0

    def predict_choice_keys(self, brain: InfantApeBrain) -> list[tuple[str, float]]:
        delib = brain.deliberation.last
        scored: list[tuple[str, float]] = []
        seen: set[str] = set()

        ordered = sorted(
            delib.contestants,
            key=lambda c: (c.selected, c.net),
            reverse=True,
        )
        for c in ordered[:5]:
            if c.key in seen:
                continue
            seen.add(c.key)
            scored.append((c.key, float(c.net)))

        goal = brain.agent_loop.goal_stack.peek()
        if goal and goal.choice_key not in seen:
            scored.append((goal.choice_key, 0.58))
            seen.add(goal.choice_key)

        if delib.limbic_winner_key and delib.limbic_winner_key not in seen:
            scored.append((delib.limbic_winner_key, 0.42))

        return sorted(scored, key=lambda x: x[1], reverse=True)

    def _fused_sensory(self, brain: InfantApeBrain) -> np.ndarray:
        sensory, _ = brain._world_sensory()
        body = brain.body.to_dict()
        room = brain.world.current_room()
        motor = brain.deliberation.motor_bias_array(brain)
        fused, _ = fuse_episodic_pattern(
            sensory,
            n=brain.n_sensory,
            body=body,
            room=room,
            motor=list(motor) if motor is not None else [],
            n_motor=brain.profile.n_motor,
        )
        return fused

    def run_tick(self, brain: InfantApeBrain) -> dict[str, Any]:
        flags = get_flags(brain)
        gov = brain.decompress_governor
        plan = self.predict_choice_keys(brain)
        self.last_plan = [k for k, _ in plan]
        self.last_regions = []
        self.chunks_warmed = 0
        self.assemblies_warmed = 0

        if flags.enable_connectome_scaffold and brain.chunk_store is not None:
            for key, _pri in plan[1:4]:
                region = brain.connectome.region_for_choice(key)
                self.last_regions.append(region)
                if brain.chunk_store.prefetch_for_focus(
                    region=region,
                    choice_key=key,
                    dim=brain.n_sensory,
                    governor=gov,
                ):
                    self.chunks_warmed += 1

        if (
            flags.enable_lobe_virtual_inject
            or brain.virtual_store.total_count() > 0
        ):
            try:
                fused = self._fused_sensory(brain)
                self.assemblies_warmed = brain.virtual_store.prefetch_for_pattern(
                    fused,
                    k=2,
                    governor=gov,
                )
            except (ValueError, TypeError):
                self.assemblies_warmed = 0

        return self.to_dict()

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan": self.last_plan[:5],
            "regions": self.last_regions[:4],
            "chunks_warmed": self.chunks_warmed,
            "assemblies_warmed": self.assemblies_warmed,
            "total_warmed": self.chunks_warmed + self.assemblies_warmed,
        }
