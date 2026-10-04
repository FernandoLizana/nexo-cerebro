"""Deterministic perturbation trigger evaluation."""

from __future__ import annotations

import hashlib

from nexo_qa.chaos.models import PerturbationSpec, TriggerSpec


def seeded_probability(spec: PerturbationSpec, *, tick: int, action_count: int) -> float:
    seed = spec.seed if spec.seed is not None else 42
    payload = f"{seed}|{spec.perturbation_id}|{tick}|{action_count}"
    digest = hashlib.sha256(payload.encode()).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def should_fire(
    trigger: TriggerSpec,
    *,
    tick: int,
    action_count: int,
    page: str | None = None,
    goal_progress: float | None = None,
    spec: PerturbationSpec | None = None,
    already_fired: bool = False,
) -> bool:
    if already_fired and (spec is None or spec.repeat_policy == "once"):
        return False
    if trigger.kind == "AT_TICK":
        return trigger.at_tick is not None and tick >= trigger.at_tick
    if trigger.kind == "AFTER_ACTION":
        return trigger.after_action_count is not None and action_count >= trigger.after_action_count
    if trigger.kind == "ON_PAGE":
        return bool(trigger.on_page and page == trigger.on_page)
    if trigger.kind == "ON_GOAL_PROGRESS":
        return goal_progress is not None and goal_progress >= float(trigger.metadata.get("min_progress", 0.5))
    if trigger.kind == "AFTER_DURATION":
        start = int(trigger.metadata.get("start_tick", 0))
        dur = trigger.after_duration_ticks or 0
        return tick >= start + dur
    if trigger.kind == "PROBABILISTIC_SEEDED" and spec is not None:
        p = trigger.probability if trigger.probability is not None else 0.5
        return seeded_probability(spec, tick=tick, action_count=action_count) < p
    return False
