"""PerturbationController — environment-only chaos injection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from nexo_qa.chaos.models import PerturbationEventType, PerturbationSpec
from nexo_qa.chaos.triggers import should_fire


@dataclass
class ActivePerturbation:
    spec: PerturbationSpec
    started_tick: int
    ends_tick: int | None = None
    injected: bool = True
    state: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerturbationController:
    """Evaluates triggers and tracks perturbation lifecycle. Does NOT mutate cognition."""

    specs: tuple[PerturbationSpec, ...]
    run_seed: int = 42
    trace_id: str = field(default_factory=lambda: uuid4().hex[:12])
    events: list[dict[str, Any]] = field(default_factory=list)
    active: dict[str, ActivePerturbation] = field(default_factory=dict)
    ended: set[str] = field(default_factory=set)
    fired: set[str] = field(default_factory=set)
    injection_coverage: dict[str, str] = field(default_factory=dict)

    def evaluate(
        self,
        *,
        tick: int,
        action_count: int,
        page: str | None = None,
        goal_progress: float | None = None,
    ) -> None:
        for spec in self.specs:
            if spec.perturbation_id in self.active or spec.perturbation_id in self.ended:
                if spec.perturbation_id in self.active:
                    ap = self.active[spec.perturbation_id]
                    if ap.ends_tick is not None and tick >= ap.ends_tick:
                        self._end(spec.perturbation_id, tick)
                continue
            if should_fire(
                spec.trigger,
                tick=tick,
                action_count=action_count,
                page=page,
                goal_progress=goal_progress,
                spec=spec,
                already_fired=spec.perturbation_id in self.fired,
            ):
                self._start(spec, tick)

    def _emit(self, event_type: PerturbationEventType, spec: PerturbationSpec, tick: int, **extra: Any) -> None:
        self.events.append(
            {
                "event_type": event_type.value,
                "perturbation_id": spec.perturbation_id,
                "type": spec.type,
                "intensity": spec.intensity,
                "duration_ticks": spec.duration_ticks,
                "target": spec.target_scope,
                "trace_id": self.trace_id,
                "tick": tick,
                **extra,
            }
        )

    def _start(self, spec: PerturbationSpec, tick: int) -> None:
        self.fired.add(spec.perturbation_id)
        ends = tick + spec.duration_ticks if spec.duration_ticks > 0 else None
        self.active[spec.perturbation_id] = ActivePerturbation(
            spec=spec,
            started_tick=tick,
            ends_tick=ends,
            state=dict(spec.parameters),
        )
        self.injection_coverage[spec.perturbation_id] = "injected"
        self._emit(PerturbationEventType.SCHEDULED, spec, tick)
        self._emit(PerturbationEventType.STARTED, spec, tick, actual_trigger_tick=tick)

    def _end(self, perturbation_id: str, tick: int) -> None:
        ap = self.active.pop(perturbation_id, None)
        if ap is None:
            return
        self.ended.add(perturbation_id)
        self._emit(PerturbationEventType.ENDED, ap.spec, tick)

    def environment_modifiers(self, *, tick: int) -> dict[str, Any]:
        """Return environment-level modifiers for the current tick."""
        mods: dict[str, Any] = {
            "block_actions": False,
            "blocked_actions": set(),
            "latency_ticks": 0,
            "transient_error": False,
            "session_expired": False,
            "visual_swap": False,
            "modal_distraction": False,
            "content_shift": False,
            "feedback_delay_ticks": 0,
            "disabled_controls": set(),
            "network_failure": False,
            "interruption_overlay": False,
        }
        for ap in self.active.values():
            spec = ap.spec
            p = spec.parameters
            if spec.type == "INTERRUPTION":
                mods["interruption_overlay"] = True
                mods["block_actions"] = True
                allowed = set(p.get("allowed_actions") or ("wait",))
                mods["blocked_actions"] = allowed
            elif spec.type == "LATENCY":
                mods["latency_ticks"] = max(mods["latency_ticks"], int(p.get("delay_ticks", spec.duration_ticks)))
            elif spec.type == "TRANSIENT_ERROR":
                mods["transient_error"] = True
                mods["transient_error_attempts"] = int(p.get("fail_attempts", 1))
            elif spec.type == "SESSION_EXPIRY":
                mods["session_expired"] = True
            elif spec.type == "VISUAL_CHANGE":
                mods["visual_swap"] = True
            elif spec.type == "MODAL_DISTRACTION":
                mods["modal_distraction"] = True
            elif spec.type == "CONTENT_SHIFT":
                mods["content_shift"] = True
            elif spec.type == "FEEDBACK_DELAY":
                mods["feedback_delay_ticks"] = max(
                    mods["feedback_delay_ticks"], int(p.get("delay_ticks", spec.duration_ticks))
                )
            elif spec.type == "CONTROL_DISABLE":
                disabled = p.get("disabled_actions") or p.get("controls") or ("activate_switch",)
                mods["disabled_controls"].update(disabled)
            elif spec.type == "NETWORK_LIKE_FAILURE":
                mods["network_failure"] = True
        return mods

    def mark_injection_failure(self, spec: PerturbationSpec, tick: int, reason: str) -> None:
        self.injection_coverage[spec.perturbation_id] = "injection_failure"
        self._emit(PerturbationEventType.INJECTION_FAILURE, spec, tick, reason=reason)

    def coverage_summary(self) -> dict[str, Any]:
        planned = len(self.specs)
        injected = sum(1 for v in self.injection_coverage.values() if v == "injected")
        failures = sum(1 for v in self.injection_coverage.values() if v == "injection_failure")
        missed = planned - injected - failures
        return {
            "planned": planned,
            "successfully_injected": injected,
            "missed": max(0, missed),
            "injection_failures": failures,
        }

    def forbidden_cognitive_tokens(self) -> tuple[str, ...]:
        """Documented boundary — controller must not reference these on agent/runtime."""
        return (
            "agent.memory",
            "agent.frustration",
            "agent.attention",
            "working_memory.clear",
            "persona_traits",
            "decision_score",
        )
