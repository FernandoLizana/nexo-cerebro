"""Task goal runtime — process, loop detection, bind helpers."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from nexo.core.events import CognitiveEvent
from nexo.core.module_protocol import ProcessContext
from nexo.core.process import BaseProcess
from nexo_qa.goals.models import Goal, GoalProgress, TaskContext
from nexo_qa.goals.progress import evaluate_progress
from nexo_qa.goals.relevance import goal_relevance_map


@dataclass
class LoopDetector:
    window: int = 8
    stagnation_threshold: int = 6
    _recent_actions: deque[str] = field(default_factory=lambda: deque(maxlen=8))
    _recent_urls: deque[str] = field(default_factory=lambda: deque(maxlen=8))

    def record(self, action: str, url: str) -> tuple[bool, bool]:
        self._recent_actions.append(action)
        self._recent_urls.append(url)
        loop = len(self._recent_actions) >= 4 and len(set(list(self._recent_actions)[-4:])) <= 2
        stagnation = len(self._recent_actions) >= self.stagnation_threshold and len(set(self._recent_urls)) <= 2
        return loop, stagnation


@dataclass
class TaskGoalProcess(BaseProcess):
    """Inject task goals into cognition — priority before PFC deliberation."""

    process_id: str = "task_goal"
    period_ticks: int = 1
    priority: int = 64

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        goal: Goal | None = context.config.get("task_goal")
        if goal is None:
            return []
        world = context.config.get("world_state")
        task_context: TaskContext = context.config.get("task_context") or TaskContext()
        tick = context.clock.tick
        t = context.clock.simulation_time
        events: list[CognitiveEvent] = []

        if goal.status == "PENDING":
            goal = goal.activate()
            context.config["task_goal"] = goal

        url = ""
        action_history: tuple[str, ...] = ()
        action_labels: dict[str, str] = {}
        if world is not None:
            snap = getattr(world, "_snapshot", None)
            url = snap.url if snap else getattr(world, "initial_url", "")
            action_history = tuple(getattr(world, "action_history", []) or [])
            if hasattr(world, "action_schemas"):
                for schema in world.action_schemas():
                    action_labels[schema.id] = schema.label

        progress = evaluate_progress(
            goal,
            url=url,
            action_history=action_history,
            action_labels=action_labels,
            task_context=task_context,
            policy_blocked=getattr(world, "last_error", None) == "POLICY_BLOCKED",
        )
        context.config["goal_progress"] = progress

        # Advance active subgoal from progress evidence (semantic, not steps)
        subgoals = list(goal.subgoals)
        if progress.level in ("none", "partial") and subgoals:
            goal.active_subgoal = subgoals[min(len(subgoals) - 1, 0 if progress.level == "none" else 1)]
        elif progress.level == "high" and len(subgoals) >= 3:
            goal.active_subgoal = subgoals[2]
        elif progress.level == "complete":
            goal.active_subgoal = subgoals[-1] if subgoals else None
        context.config["task_goal"] = goal

        relevance: dict[str, float] = {}
        if world is not None and hasattr(world, "action_schemas"):
            actions = tuple(
                (s.id, s.label, s.affordance) for s in world.action_schemas()
            )
            relevance = goal_relevance_map(goal, actions)
        context.config["goal_relevance"] = relevance

        salience_map: dict[str, float] = {}
        if world is not None and hasattr(world, "action_salience_map"):
            salience_map = world.action_salience_map()
        context.config["action_salience"] = salience_map

        detector: LoopDetector = context.config.setdefault("goal_loop_detector", LoopDetector())
        if action_history:
            loop, stagnation = detector.record(action_history[-1], url)
            if loop:
                events.append(
                    CognitiveEvent(
                        event_type="goal.behavior_loop",
                        source=self.process_id,
                        tick=tick,
                        simulation_time=t,
                        payload={"recent_actions": list(detector._recent_actions)[-4:]},
                    )
                )
            if stagnation:
                events.append(
                    CognitiveEvent(
                        event_type="goal.drift",
                        source=self.process_id,
                        tick=tick,
                        simulation_time=t,
                        payload={"url": url, "progress": progress.to_dict()},
                    )
                )

        task_tokens = goal.goal_tokens()
        merged_goals = ("survive",) + task_tokens
        events.append(
            CognitiveEvent(
                event_type="goals.updated",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={"goals": merged_goals, "source": "TASK_GOAL"},
            )
        )
        events.append(
            CognitiveEvent(
                event_type="goal.progress",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "goal_id": goal.goal_id,
                    "progress": progress.to_dict(),
                    "active_subgoal": goal.active_subgoal,
                    "instruction_source": "TASK_GOAL",
                },
            )
        )
        if relevance:
            top = sorted(relevance.items(), key=lambda kv: kv[1], reverse=True)[:5]
            events.append(
                CognitiveEvent(
                    event_type="goal.relevance",
                    source=self.process_id,
                    tick=tick,
                    simulation_time=t,
                    payload={"top_actions": top, "instruction_source": "TASK_GOAL"},
                )
            )
        return events


def bind_task(
    runtime: Any,
    *,
    goal: Goal,
    task_context: TaskContext | None = None,
    world: Any | None = None,
) -> Any:
    """Wire task goal into IntegratedRuntime scheduler config."""
    if world is not None:
        runtime.world = world
        runtime.scheduler.config["world_state"] = world
        if hasattr(world, "goal"):
            world.goal = goal.description
    runtime.scheduler.config["task_goal"] = goal
    runtime.scheduler.config["task_context"] = task_context or TaskContext()
    if not runtime.scheduler.config.get("_task_goal_process_registered"):
        runtime.scheduler.register(TaskGoalProcess())
        runtime.scheduler.config["_task_goal_process_registered"] = True
    return runtime
