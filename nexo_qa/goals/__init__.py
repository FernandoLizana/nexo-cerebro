"""NEXO Cognitive QA — goal semantics (P4)."""

from __future__ import annotations

from nexo_qa.goals.context import task_context_from_mapping
from nexo_qa.goals.models import Goal, GoalProgress, TaskContext
from nexo_qa.goals.parser import parse_goal
from nexo_qa.goals.progress import evaluate_progress
from nexo_qa.goals.relevance import goal_relevance_for_text, goal_relevance_map
from nexo_qa.goals.runtime import LoopDetector, TaskGoalProcess, bind_task

__all__ = [
    "Goal",
    "TaskContext",
    "GoalProgress",
    "TaskGoalProcess",
    "LoopDetector",
    "parse_goal",
    "evaluate_progress",
    "goal_relevance_for_text",
    "goal_relevance_map",
    "task_context_from_mapping",
    "bind_task",
]
