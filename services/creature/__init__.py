"""NEXO Creature Engine (S4) — lightweight synthetic animals without LLM.

Uses FSM + utility AI + associative memory. Experimental drives only;
not claims of animal consciousness or validated ethology.
"""

from __future__ import annotations

from services.creature.engine import CreatureEngine, CreatureTickResult, run_creature_ticks
from services.creature.fsm import CreatureState
from services.creature.memory import AssociativeMemory

__all__ = [
    "AssociativeMemory",
    "CreatureEngine",
    "CreatureState",
    "CreatureTickResult",
    "run_creature_ticks",
]
