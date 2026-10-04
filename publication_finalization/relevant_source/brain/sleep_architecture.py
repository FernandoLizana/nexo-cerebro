"""
Arquitectura de sueño NREM/REM + replay SWR (Brain Facts Ch.9).

Ciclos: NREM ligero → NREM profundo (consolidación) → REM (integración emocional).

``replay_mode``:
  - default: pesos actuales (paper E3)
  - uniform: muestreo equiprobable
  - selective: prioriza |valence| + olvido activo de engramas fríos en NREM light

El sueño **no** selecciona acciones en vigilia (libre albedrío / agency intacto).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import numpy as np

from .consolidation import consolidate_to_cortex
from .experiment_flags import get_flags

if TYPE_CHECKING:
    from .mind import InfantApeBrain

CYCLE_PHASES: tuple[str, ...] = ("nrem_light", "nrem_deep", "nrem_deep", "rem")


@dataclass
class SleepCycleStats:
    phase: str
    replays: int = 0
    swr_bursts: int = 0
    consolidated: int = 0
    dream_fragments: int = 0


@dataclass
class SleepArchitecture:
    last_phase: str = "awake"
    cycles_completed: int = 0
    total_replays: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)
    last_replay_mode: str = "default"

    def run(
        self,
        brain: InfantApeBrain,
        *,
        cycles: int = 3,
        steps_per_cycle: int = 120,
        replay_mode: str | None = None,
    ) -> dict[str, Any]:
        cycles = max(1, min(cycles, 8))
        steps_per_cycle = max(40, min(steps_per_cycle, 200))
        flags = get_flags(brain)
        mode = (replay_mode or "").strip().lower()
        if not mode:
            mode = "selective" if flags.enable_selective_sleep else "default"
        self.last_replay_mode = mode

        replays = 0
        consolidated: list[dict] = []
        virtual_ingested: list[str] = []
        labels_replayed: list[str] = []
        replay_weights: list[float] = []
        phase_log: list[dict[str, Any]] = []
        swr_total = 0
        forgotten = 0

        replay_mods = SimpleNamespace(
            acetylcholine=brain.modulators.acetylcholine,
            cortisol=brain.hypothalamus.cortisol,
        )

        for cycle_i in range(cycles):
            for phase in CYCLE_PHASES:
                stats = SleepCycleStats(phase=phase)
                self.last_phase = phase
                brain.brain_states.state = phase
                ach_base = brain.modulators.acetylcholine

                if phase == "nrem_light":
                    brain.modulators.acetylcholine = float(np.clip(ach_base * 0.55, 0.08, 0.45))
                    brain.thalamus.arousal_gate = 0.35
                    step_scale = 0.4
                    consolidate = False
                    swr = False
                    if mode in ("selective", "emotion", "emotional"):
                        forgotten += brain.memory_store.active_forgetting_pass(
                            max_abs_valence=0.22, min_count=1
                        )
                elif phase == "nrem_deep":
                    brain.modulators.acetylcholine = float(np.clip(ach_base * 0.35, 0.05, 0.3))
                    brain.thalamus.arousal_gate = 0.22
                    step_scale = 0.55
                    consolidate = True
                    swr = True
                else:  # rem
                    brain.modulators.acetylcholine = float(
                        np.clip(ach_base * 1.15 + 0.12, 0.35, 0.95)
                    )
                    brain.thalamus.arousal_gate = 0.48
                    step_scale = 0.35
                    consolidate = False
                    swr = False
                    brain.modulators.serotonin = float(
                        np.clip(brain.modulators.serotonin + 0.04, 0, 1)
                    )

                mem = brain.hippocampus.sample_for_replay(
                    sleep_pressure=brain.brainstem.sleep_pressure,
                    modulators=replay_mods,
                    sleep_phase=phase,
                    replay_mode=mode,
                )
                sensory = np.zeros(brain.n_sensory, dtype=np.float32)
                if mem is not None:
                    sensory = np.asarray(
                        mem.get("pattern", mem.get("sensory")), dtype=np.float32
                    )
                    replays += 1
                    stats.replays = 1
                    lbl = mem.get("label", "?")[:40]
                    labels_replayed.append(lbl)
                    replay_weights.append(float(mem.get("replay_weight", 0)))
                    mem_key = mem.get("key")
                    if mem_key:
                        brain.memory_store.record_sleep_replay(str(mem_key))

                    if swr:
                        for _ in range(3):
                            brain._simulate(sensory, total_steps=max(8, steps_per_cycle // 12))
                            swr_total += 1
                            stats.swr_bursts += 1
                    else:
                        brain._simulate(sensory, total_steps=int(steps_per_cycle * step_scale))

                    if consolidate:
                        cortex_pat = mem.get("sensory", sensory)
                        cstats = consolidate_to_cortex(
                            brain.cortex,
                            cortex_pat,
                            valence=float(mem.get("valence", 0)),
                            strength=min(1.8, 0.9 + 0.12 * mem.get("count", 1)),
                        )
                        cstats["label"] = mem.get("label", "")[:50]
                        cstats["room"] = mem.get("room", "")
                        cstats["phase"] = phase
                        consolidated.append(cstats)
                        stats.consolidated = 1
                        brain.typed_memory.consolidate_semantic_from_episode(brain, mem)

                    if phase == "rem":
                        stats.dream_fragments = 1
                        brain.typed_memory.tag_emotional_memory(mem)

                    asm = brain.virtual_store.ingest(
                        mem.get("pattern", sensory),
                        label=mem.get("label", "replay")[:60],
                        modality=mem.get("modality", "world"),
                        valence=float(mem.get("valence", 0)),
                        arousal=float(mem.get("arousal", 0)),
                        strength=min(1.0, 0.45 + 0.08 * mem.get("count", 1)),
                    )
                    if asm:
                        virtual_ingested.append(asm.get("label", "?")[:40])
                else:
                    brain._simulate(sensory, total_steps=int(steps_per_cycle * step_scale * 0.5))

                brain.brainstem.rest(0.06 if phase != "rem" else 0.04)
                phase_log.append(
                    {
                        "cycle": cycle_i + 1,
                        "phase": phase,
                        "replays": stats.replays,
                        "swr": stats.swr_bursts,
                        "consolidated": stats.consolidated,
                    }
                )

        self.cycles_completed += cycles
        self.total_replays += replays
        self.history.extend(phase_log[-16:])
        self.last_phase = "awake"
        brain.brain_states.state = "awake"

        affordance_sleep = {}
        if get_flags(brain).enable_affordance_learning and hasattr(brain, "affordance_map"):
            affordance_sleep = brain.affordance_map.consolidate_during_sleep()

        return {
            "replays": replays,
            "swr_bursts": swr_total,
            "consolidation": consolidated,
            "labels_replayed": labels_replayed,
            "replay_weights": replay_weights,
            "virtual_ingested": virtual_ingested,
            "phase_log": phase_log,
            "sleep_mode": f"nrem_rem_{mode}",
            "replay_mode": mode,
            "active_forgetting": forgotten,
            "affordance_sleep": affordance_sleep,
            "agency_note": "Sleep consolidates memory only; does not select waking actions",
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_phase": self.last_phase,
            "cycles_completed": self.cycles_completed,
            "total_replays": self.total_replays,
            "last_replay_mode": self.last_replay_mode,
            "recent_phases": self.history[-8:],
        }
