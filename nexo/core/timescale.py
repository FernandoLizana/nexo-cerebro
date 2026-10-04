"""Escalas temporales de procesos cognitivos."""

from __future__ import annotations

from enum import IntEnum


class Timescale(IntEnum):
    REFLEX = 1
    SENSORY = 1
    INTEROCEPTION = 2
    ATTENTION = 2
    DELIBERATION = 5
    PLANNING = 10
    CONSOLIDATION = 100
    DEVELOPMENT = 1000


DEFAULT_PERIODS: dict[str, int] = {
    "sensory_relay": Timescale.SENSORY,
    "interoception": Timescale.INTEROCEPTION,
    "attention": Timescale.ATTENTION,
    "working_memory": Timescale.ATTENTION,
    "deliberation": Timescale.DELIBERATION,
    "planning": Timescale.PLANNING,
    "consolidation": Timescale.CONSOLIDATION,
    "development": Timescale.DEVELOPMENT,
}
