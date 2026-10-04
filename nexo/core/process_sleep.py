"""Procesos Sprint 9 — sueño, consolidación y desarrollo."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.body.circadian import CircadianClock
from nexo.core.events import CognitiveEvent
from nexo.core.module_protocol import ProcessContext
from nexo.core.process import BaseProcess
from nexo.development.tracker import DevelopmentTracker
from nexo.memory.consolidation import MemoryConsolidator
from nexo.memory.hippocampus.store import HippocampalStore
from nexo.sleep.architecture import SleepArchitecture


def _memory_rng(context: ProcessContext):
    return context.config.get("memory_rng") or context.rng


@dataclass
class SleepArchitectureProcess(BaseProcess):
    """Gestión de fases de sueño según presión homeostática."""

    process_id: str = "sleep_architecture"
    period_ticks: int = 5
    priority: int = 76

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        hctrl = context.config.get("homeostatic_controller")
        if hctrl is None:
            return []
        arch: SleepArchitecture = context.config.setdefault("sleep_architecture", SleepArchitecture())
        t = context.clock.simulation_time
        circ = CircadianClock.from_simulation_seconds(t)
        prev = arch.phase
        phase = arch.update(
            sleep_pressure=hctrl.body.sleep_pressure,
            alertness=circ.alertness(),
            tick=context.clock.tick,
            fatigue=hctrl.body.fatigue,
        )
        context.config["sleep_phase"] = phase
        context.config["sleep_active"] = arch.is_sleeping

        if phase == prev:
            return []
        tick = context.clock.tick
        return [
            CognitiveEvent(
                event_type="sleep.phase_changed",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={"phase": phase, "alertness": round(circ.alertness(), 4), **arch.to_dict()},
            )
        ]


@dataclass
class MemoryReplayProcess(BaseProcess):
    """Replay hipocampal durante sueño."""

    process_id: str = "memory_replay"
    period_ticks: int = 3
    priority: int = 48

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        arch: SleepArchitecture | None = context.config.get("sleep_architecture")
        store: HippocampalStore | None = context.config.get("hippocampal_store")
        if arch is None or store is None or not arch.allows_replay or not store.episodes:
            return []

        samples = store.sample_for_replay(rng=_memory_rng(context), n=1)
        if not samples:
            return []
        ep = samples[0]
        arch.total_replays += 1
        tick = context.clock.tick
        t = context.clock.simulation_time
        return [
            CognitiveEvent(
                event_type="memory.replayed",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "episode_id": ep.episode_id,
                    "action": ep.action,
                    "modality": ep.modality,
                    "confidence": ep.confidence,
                    "phase": arch.phase,
                },
            )
        ]


@dataclass
class ConsolidationProcess(BaseProcess):
    """Consolidación en NREM profundo."""

    process_id: str = "memory_consolidation"
    period_ticks: int = 5
    priority: int = 47

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        arch: SleepArchitecture | None = context.config.get("sleep_architecture")
        store: HippocampalStore | None = context.config.get("hippocampal_store")
        consolidator: MemoryConsolidator = context.config.setdefault(
            "memory_consolidator", MemoryConsolidator()
        )
        dev: DevelopmentTracker | None = context.config.get("development_tracker")
        if arch is None or store is None or not arch.allows_consolidation:
            return []

        samples = store.sample_for_replay(rng=_memory_rng(context), n=1, min_confidence=0.15)
        if not samples:
            return []
        ep = samples[0]
        if ep.episode_id in consolidator.consolidated_ids:
            return []

        consolidated = consolidator.consolidate(ep)
        store.replace_episode(consolidated)
        arch.total_consolidated += 1
        if dev is not None:
            dev.register_consolidation()

        plasticity = context.router.plasticity
        plasticity.update("hippocampus", "prefrontal", 0.03)

        tick = context.clock.tick
        t = context.clock.simulation_time
        return [
            CognitiveEvent(
                event_type="memory.consolidated",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "episode_id": consolidated.episode_id,
                    "confidence": consolidated.confidence,
                    "phase": arch.phase,
                },
            )
        ]


@dataclass
class DevelopmentProcess(BaseProcess):
    """Maduración cognitiva lenta."""

    process_id: str = "development"
    period_ticks: int = 20
    priority: int = 46

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        dev: DevelopmentTracker = context.config.setdefault("development_tracker", DevelopmentTracker())
        dev.tick(simulation_tick=context.clock.tick)
        tick = context.clock.tick
        return [
            CognitiveEvent(
                event_type="development.updated",
                source=self.process_id,
                tick=tick,
                simulation_time=context.clock.simulation_time,
                payload=dev.to_dict(),
            )
        ]
