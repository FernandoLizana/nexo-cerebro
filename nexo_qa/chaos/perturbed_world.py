"""ChaoticMockWorld — wraps MockWorld with environment perturbations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nexo_qa.chaos.controller import PerturbationController
from nexo_qa.chaos.models import PerturbationSpec
from nexo_qa.testing.mock_world import MockWorld


@dataclass
class ChaoticMockWorld:
    """Environment wrapper. Perturbations affect world/perception only — not persona traits."""

    inner: MockWorld
    controller: PerturbationController
    trace_log: list[dict[str, Any]] = field(default_factory=list)
    _pending_feedback: list[dict[str, Any]] = field(default_factory=list)
    _latency_remaining: int = 0
    _transient_failures: dict[str, int] = field(default_factory=dict)
    _session_snapshotted: bool = False
    _pre_session_phase: str | None = None
    _visual_swapped: bool = False
    _interruption_end_tick: int | None = None
    _recovery_start_tick: int | None = None
    _recovery_measured: int | None = None
    goal_preserved: bool = True
    _event_cursor: int = 0

    @classmethod
    def create(
        cls,
        *,
        seed: int,
        perturbations: tuple[PerturbationSpec, ...] = (),
        trace_id: str | None = None,
    ) -> ChaoticMockWorld:
        ctrl = PerturbationController(specs=perturbations, run_seed=seed, trace_id=trace_id or f"chaos-{seed}")
        return cls(inner=MockWorld(seed=seed), controller=ctrl)

    @property
    def seed(self) -> int:
        return self.inner.seed

    @property
    def phase(self) -> str:
        return self.inner.phase

    @property
    def ticks(self) -> int:
        return self.inner.ticks

    @property
    def action_history(self) -> list[str]:
        return self.inner.action_history

    @property
    def episodes(self) -> list[str]:
        return self.inner.episodes

    @property
    def last_error(self) -> str | None:
        return self.inner.last_error

    def sync_from_body(self, body: object) -> None:
        self.inner.sync_from_body(body)

    def available_actions(self) -> tuple[str, ...]:
        actions = self.inner.available_actions()
        mods = self.controller.environment_modifiers(tick=self.inner.ticks)
        disabled = set(mods.get("disabled_controls") or ())
        if mods.get("interruption_overlay"):
            allowed = set(mods.get("blocked_actions") or ("wait",))
            return tuple(a for a in actions if a in allowed)
        return tuple(a for a in actions if a not in disabled)

    def action_info(self, action: str) -> dict[str, Any]:
        return self.inner.action_info(action)

    def action_schemas(self) -> tuple[Any, ...]:
        return self.inner.action_schemas()

    def percepts_for_agent(self) -> list[tuple[str, float, tuple[float, ...]]]:
        self.controller.evaluate(tick=self.inner.ticks, action_count=len(self.inner.action_history))
        percepts = list(self.inner.percepts_for_agent())
        mods = self.controller.environment_modifiers(tick=self.inner.ticks)
        if mods.get("interruption_overlay"):
            percepts.insert(0, ("interruption_overlay", 0.95, (1.0, 0.0, 0.0)))
        if mods.get("modal_distraction"):
            percepts.insert(0, ("promotion_modal", 0.92, (1.0, 0.5, 0.0)))
        if mods.get("content_shift"):
            percepts.append(("banner_shift", 0.7, (0.8, 0.8, 0.2)))
        if mods.get("visual_swap") or self._visual_swapped:
            percepts = self._swap_visual_percepts(percepts)
        if mods.get("session_expired"):
            percepts.insert(0, ("session_expired_notice", 0.88, (0.9, 0.1, 0.1)))
        if self._latency_remaining > 0:
            percepts.append(("loading_spinner", 0.75, (0.5, 0.5, 0.5)))
        return percepts

    def _swap_visual_percepts(self, percepts: list[tuple[str, float, tuple[float, ...]]]) -> list[tuple[str, float, tuple[float, ...]]]:
        out: list[tuple[str, float, tuple[float, ...]]] = []
        for name, sal, coords in percepts:
            if name == "panel":
                out.append(("switch", sal, coords))
            elif name == "switch":
                out.append(("panel", sal, coords))
            else:
                out.append((name, sal, coords))
        self._visual_swapped = True
        return out

    def apply_action(self, action: str) -> dict[str, Any]:
        tick = self.inner.ticks
        action_count = len(self.inner.action_history)
        self.controller.evaluate(tick=tick, action_count=action_count)
        mods = self.controller.environment_modifiers(tick=tick)

        if mods.get("interruption_overlay") and action not in set(mods.get("blocked_actions") or ("wait",)):
            result = self._reject(action, "interruption_blocking")
            self._append_trace(result)
            return result

        if action not in self.available_actions():
            result = self._reject(action, "control_disabled" if mods.get("disabled_controls") else "action_unavailable")
            self._append_trace(result)
            return result

        if mods.get("latency_ticks") and self._latency_remaining <= 0:
            self._latency_remaining = int(mods["latency_ticks"])
        if self._latency_remaining > 0:
            self._latency_remaining -= 1
            self.inner.ticks += 1
            result = {
                "reward": 0.0,
                "homeostatic_deltas": {},
                "encoded_memory": None,
                "accepted": False,
                "success": False,
                "error": "latency_pending",
                "latency_remaining": self._latency_remaining,
            }
            self._append_trace(result)
            return result

        fail_key = action
        if mods.get("transient_error") or mods.get("network_failure"):
            remaining = self._transient_failures.get(fail_key, int(mods.get("transient_error_attempts", 1)))
            if remaining > 0:
                self._transient_failures[fail_key] = remaining - 1
                err = "network_like_failure" if mods.get("network_failure") else "transient_error"
                result = self._reject(action, err)
                self._append_trace(result)
                return result

        if mods.get("session_expired") and not self._session_snapshotted:
            self._pre_session_phase = self.inner.phase
            self.inner.phase = "closed"
            self._session_snapshotted = True
            self.trace_log.append({"event": "session_expired", "tick": tick, "site_state_lost": True})

        delay = int(mods.get("feedback_delay_ticks") or 0)
        result = self.inner.apply_action(action)
        if delay > 0 and result.get("accepted"):
            pending = dict(result)
            pending["feedback_delayed"] = True
            pending["visible_success"] = False
            self._pending_feedback.append(pending)
            visible = dict(result)
            visible["success"] = False
            visible["reward"] = 0.0
            visible["error"] = "feedback_pending"
            self._append_trace(visible)
            return visible

        self._measure_recovery(result)
        self._append_trace(result)
        self._flush_pending_feedback()
        return result

    def _reject(self, action: str, error: str) -> dict[str, Any]:
        self.inner.ticks += 1
        self.inner.last_error = error
        return {
            "reward": 0.0,
            "homeostatic_deltas": {},
            "encoded_memory": None,
            "accepted": False,
            "success": False,
            "error": error,
        }

    def _measure_recovery(self, result: dict[str, Any]) -> None:
        if self._interruption_end_tick is None:
            for ev in reversed(self.controller.events):
                if ev.get("event_type") == "PERTURBATION_ENDED" and ev.get("type") == "INTERRUPTION":
                    self._interruption_end_tick = int(ev.get("tick", 0))
                    self._recovery_start_tick = self.inner.ticks
                    break
        if self._recovery_start_tick is not None and self._recovery_measured is None:
            if result.get("success") and result.get("to_phase") != result.get("from_phase"):
                self._recovery_measured = self.inner.ticks - self._recovery_start_tick

    def _flush_pending_feedback(self) -> None:
        if self._pending_feedback:
            self.trace_log.extend({"event": "feedback_released", "payload": self._pending_feedback.pop(0)})

    def _append_trace(self, result: dict[str, Any]) -> None:
        self.trace_log.append({"tick": self.inner.ticks, "action_result": result})
        self.trace_log.extend(self.controller.events[self._event_cursor :])
        self._event_cursor = len(self.controller.events)

    def injection_coverage(self) -> dict[str, Any]:
        return self.controller.coverage_summary()

    def perturbation_events(self) -> list[dict[str, Any]]:
        return list(self.controller.events)

    def interruption_recovery_ticks(self) -> int | None:
        return self._recovery_measured
