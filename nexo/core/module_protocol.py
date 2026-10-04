"""Protocolo y contexto de procesos cognitivos."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

import numpy as np

from nexo.core.clock import SimulationClock
from nexo.core.events import CognitiveEvent
from nexo.core.messages import MessageBus
from nexo.core.state_store import StateStore
from nexo.connectome.routing import ConnectomeRouter


@dataclass
class ProcessContext:
    clock: SimulationClock
    state_store: StateStore
    message_bus: MessageBus
    router: ConnectomeRouter
    rng: np.random.Generator
    config: dict[str, Any] = field(default_factory=dict)
    telemetry: Any | None = None
    legacy_brain: Any | None = None


class CognitiveProcess(Protocol):
    process_id: str
    period_ticks: int
    phase_offset: int
    priority: int

    def step(self, context: ProcessContext) -> list[CognitiveEvent]: ...
