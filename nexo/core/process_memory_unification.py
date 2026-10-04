"""Promoción hippo → SQLite tras consolidación (Fase 14)."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext
from nexo.demo.memory_unification import promote_episode_to_legacy
from nexo.memory.consolidation import MemoryConsolidator
from nexo.memory.hippocampus.store import HippocampalStore


@dataclass
class MemoryUnificationProcess(BaseProcess):
    process_id: str = "memory_unification"
    period_ticks: int = 5
    priority: int = 45

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("memory_unification_mode") != "integrated":
            return []
        brain = context.legacy_brain
        store: HippocampalStore | None = context.config.get("hippocampal_store")
        consolidator: MemoryConsolidator | None = context.config.get("memory_consolidator")
        if brain is None or store is None or consolidator is None:
            return []

        promoted: set[str] = context.config.setdefault("_memory_unified_ids", set())
        pending = consolidator.consolidated_ids - promoted
        if not pending:
            return []

        tick = context.clock.tick
        t = context.clock.simulation_time
        out: list[CognitiveEvent] = []
        for episode_id in list(pending):
            episode = next((ep for ep in store.episodes if ep.episode_id == episode_id), None)
            if episode is None:
                continue
            result = promote_episode_to_legacy(brain, episode)
            if result.get("promoted"):
                promoted.add(episode_id)
            out.append(
                CognitiveEvent(
                    event_type="memory.unified",
                    source=self.process_id,
                    tick=tick,
                    simulation_time=t,
                    payload=result,
                )
            )
        return out
