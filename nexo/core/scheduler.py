"""Scheduler cognitivo multiescala con prioridades."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from nexo.core.clock import SimulationClock
from nexo.core.events import CognitiveEvent
from nexo.core.messages import MessageBus
from nexo.core.module_protocol import CognitiveProcess, ProcessContext
from nexo.core.state_store import StateStore
from nexo.connectome.routing import ConnectomeRouter
from nexo.telemetry.recorder import TelemetryRecorder


@dataclass
class ProcessRegistration:
    process: CognitiveProcess
    enabled: bool = True


@dataclass
class CognitiveScheduler:
    """Coordina procesos recurrentes sobre estado compartido."""

    clock: SimulationClock
    state_store: StateStore
    router: ConnectomeRouter
    rng: np.random.Generator
    message_bus: MessageBus = field(default_factory=MessageBus)
    processes: list[ProcessRegistration] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    telemetry: TelemetryRecorder | None = None
    legacy_brain: Any | None = None
    _cycle_count: int = 0

    def register(self, process: CognitiveProcess, *, enabled: bool = True) -> None:
        self.processes.append(ProcessRegistration(process=process, enabled=enabled))

    def _context(self) -> ProcessContext:
        return ProcessContext(
            clock=self.clock,
            state_store=self.state_store,
            message_bus=self.message_bus,
            router=self.router,
            rng=self.rng,
            config=self.config,
            telemetry=self.telemetry,
            legacy_brain=self.legacy_brain,
        )

    def step(self) -> list[CognitiveEvent]:
        tick = self.clock.tick
        deliveries = self.router.advance_tick(tick)
        self.config["connectome_deliveries"] = deliveries
        all_events: list[CognitiveEvent] = []
        ctx = self._context()

        for msg in self.message_bus.deliver(tick):
            all_events.append(
                CognitiveEvent(
                    event_type="message.delivered",
                    source=msg.source,
                    target=msg.target,
                    tick=tick,
                    simulation_time=self.clock.simulation_time,
                    payload={"signal_type": msg.signal_type, **msg.payload},
                )
            )

        active: list[tuple[int, CognitiveProcess]] = []
        for reg in self.processes:
            if not reg.enabled:
                continue
            proc = reg.process
            should = getattr(proc, "should_run", None)
            if should and not should(tick):
                continue
            elif not should:
                period = max(1, int(getattr(proc, "period_ticks", 1)))
                offset = int(getattr(proc, "phase_offset", 0))
                if (tick - offset) % period != 0:
                    continue
            active.append((int(getattr(proc, "priority", 50)), proc))

        for _, proc in sorted(active, key=lambda x: -x[0]):
            pid = getattr(proc, "process_id", proc.__class__.__name__)
            try:
                emitted = proc.step(ctx)
            except Exception as exc:
                if self.telemetry:
                    self.telemetry.record_error(pid, str(exc), tick)
                continue
            for ev in emitted:
                self.state_store.dispatch(ev)
                all_events.append(ev)
            if self.telemetry:
                self.telemetry.record_process(pid, tick, len(emitted))

        self.clock.advance(1)
        self.state_store.state = self.state_store.state.with_tick(
            self.clock.tick, self.clock.simulation_time
        )
        self._cycle_count += 1
        if self.telemetry:
            self.telemetry.record_tick(self.clock.tick, self.state_store.state)
        return all_events

    def run(self, n_ticks: int) -> list[CognitiveEvent]:
        log: list[CognitiveEvent] = []
        for _ in range(max(1, n_ticks)):
            log.extend(self.step())
        return log

    @property
    def cycle_count(self) -> int:
        return self._cycle_count
