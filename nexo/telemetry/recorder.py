"""Registro de telemetría por tick y proceso."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class TelemetryLevel(IntEnum):
    NONE = 0
    SUMMARY = 1
    STANDARD = 2
    DEBUG = 3
    FULL = 4


@dataclass
class TelemetryRecorder:
    level: TelemetryLevel = TelemetryLevel.SUMMARY
    tick_summaries: list[dict[str, Any]] = field(default_factory=list)
    process_counts: dict[str, int] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    max_ticks: int = 2000

    def record_tick(self, tick: int, state: Any) -> None:
        if self.level == TelemetryLevel.NONE:
            return
        if self.level >= TelemetryLevel.SUMMARY:
            self.tick_summaries.append(
                {
                    "tick": tick,
                    "energy": getattr(getattr(state, "homeostatic", None), "energy", None),
                    "action": getattr(state, "current_action", None),
                    "focus": getattr(state, "attention_focus", ()),
                }
            )
            if len(self.tick_summaries) > self.max_ticks:
                self.tick_summaries = self.tick_summaries[-self.max_ticks :]

    def record_process(self, process_id: str, tick: int, events_emitted: int) -> None:
        if self.level >= TelemetryLevel.STANDARD:
            self.process_counts[process_id] = self.process_counts.get(process_id, 0) + events_emitted

    def record_error(self, process_id: str, message: str, tick: int) -> None:
        self.errors.append({"process": process_id, "tick": tick, "message": message})

    def summary(self) -> dict[str, Any]:
        return {
            "ticks_recorded": len(self.tick_summaries),
            "process_event_counts": dict(self.process_counts),
            "errors": len(self.errors),
        }
