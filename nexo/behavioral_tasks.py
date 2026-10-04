"""Tareas conductuales con métricas primarias observables externas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE
from nexo.experiment_conditions import get_condition


@dataclass
class BehavioralTaskResult:
    task_id: str
    condition: str
    seed: int
    primary_metrics: dict[str, float]
    secondary_metrics: dict[str, float] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "condition": self.condition,
            "seed": self.seed,
            "primary_metrics": self.primary_metrics,
            "secondary_metrics": self.secondary_metrics,
            "details": self.details,
        }


def _make_brain(condition: str, seed: int) -> InfantApeBrain:
    cond = get_condition(condition)
    return InfantApeBrain(
        profile=COMPACT_PROFILE,
        headless=True,
        auto_save=False,
        seed=seed,
        condition_id=cond.condition_id,
        experiment_flags=cond.flags,
    )


def task_distraction_control(*, condition: str, seed: int, steps: int = 25) -> BehavioralTaskResult:
    """Meta: llegar a target; distractor novedoso compite."""
    brain = _make_brain(condition, seed)
    brain.world.agent_x = 100.0
    brain.world.agent_y = 200.0
    target_x, target_y = 400.0, 200.0
    goal_key = "wander"
    distractor_selections = 0
    harmful = 0
    ticks_to_goal = steps
    reached = False
    for t in range(steps):
        out = brain.world_tick(steps=1)
        delib = out.get("deliberation") or {}
        ck = delib.get("choice_key", "")
        if ck in ("tv", "research"):
            distractor_selections += 1
            harmful += 1
        ax = brain.world.agent_x
        if abs(ax - target_x) < 30 and not reached:
            reached = True
            ticks_to_goal = t + 1
    return BehavioralTaskResult(
        task_id="distraction_control",
        condition=condition,
        seed=seed,
        primary_metrics={
            "goal_success": 1.0 if reached else 0.0,
            "ticks_to_goal": float(ticks_to_goal),
            "distractor_selections": float(distractor_selections),
            "harmful_action_selected": float(harmful),
            "reward_obtained": 1.0 if reached else 0.0,
        },
        secondary_metrics={},
        details={"target_x": target_x, "steps": steps},
    )


def task_reward_reversal(*, condition: str, seed: int, steps: int = 30) -> BehavioralTaskResult:
    """Acción A recompensada antes del tick reversal; B después."""
    brain = _make_brain(condition, seed)
    reversal_tick = steps // 2
    reward_a = reward_b = 0.0
    pre_correct = pre_total = post_correct = post_total = 0
    perseverative = 0
    last_choice = ""
    for t in range(steps):
        out = brain.world_tick(steps=1)
        ck = (out.get("deliberation") or {}).get("choice_key", "")
        if t < reversal_tick:
            pre_total += 1
            if ck in ("eat", "harvest"):
                pre_correct += 1
                reward_a += 1.0
            if ck == "drink":
                perseverative += 1
        else:
            post_total += 1
            if ck in ("drink", "rest"):
                post_correct += 1
                reward_b += 1.0
            if ck in ("eat", "harvest") and last_choice in ("eat", "harvest"):
                perseverative += 1
        last_choice = ck
    return BehavioralTaskResult(
        task_id="reward_reversal",
        condition=condition,
        seed=seed,
        primary_metrics={
            "pre_reversal_accuracy": pre_correct / max(pre_total, 1),
            "post_reversal_accuracy": post_correct / max(post_total, 1),
            "trials_to_adapt": float(reversal_tick),
            "perseverative_errors": float(perseverative),
            "total_reward": reward_a + reward_b,
        },
        secondary_metrics={},
        details={"reversal_tick": reversal_tick},
    )
