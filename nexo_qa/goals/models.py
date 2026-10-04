"""Goal and task models — declarative, step-free, serializable."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

GoalStatus = Literal[
    "PENDING",
    "ACTIVE",
    "BLOCKED",
    "PARTIALLY_SATISFIED",
    "SATISFIED",
    "FAILED",
    "ABANDONED",
]

ProgressLevel = Literal["unknown", "none", "partial", "high", "complete", "blocked"]

InstructionSource = Literal["SYSTEM", "TASK_GOAL", "TASK_CONTEXT", "WEB_CONTENT"]


@dataclass(frozen=True, slots=True)
class TaskContext:
    """Agent-visible task data — no oracle, selectors, or next-step hints."""

    user_name: str = ""
    email: str = ""
    desired_plan: str = ""
    locale: str = "es"
    extra: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_name": self.user_name,
            "email": self.email,
            "desired_plan": self.desired_plan,
            "locale": self.locale,
            "extra": dict(self.extra),
        }

    def agent_dict(self) -> dict[str, Any]:
        """Cognitive-safe serialization — no oracle keys."""
        return self.to_dict()


@dataclass
class Goal:
    goal_id: str
    description: str
    goal_type: str = "general"
    status: GoalStatus = "PENDING"
    priority: float = 1.0
    constraints: dict[str, Any] = field(default_factory=dict)
    entities: dict[str, str] = field(default_factory=dict)
    subgoals: tuple[str, ...] = ()
    active_subgoal: str | None = None
    parent_goal_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    instruction_source: InstructionSource = "TASK_GOAL"

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "description": self.description,
            "goal_type": self.goal_type,
            "status": self.status,
            "priority": self.priority,
            "constraints": dict(self.constraints),
            "entities": dict(self.entities),
            "subgoals": list(self.subgoals),
            "active_subgoal": self.active_subgoal,
            "parent_goal_id": self.parent_goal_id,
            "metadata": dict(self.metadata),
            "instruction_source": self.instruction_source,
        }

    def activate(self) -> Goal:
        from dataclasses import replace

        return replace(self, status="ACTIVE")

    def goal_tokens(self) -> tuple[str, ...]:
        """Symbolic tokens for active_goals — no steps."""
        tokens: list[str] = ["task:active", f"task:type:{self.goal_type}"]
        for key, value in self.entities.items():
            if value:
                tokens.append(f"task:{key}:{value.lower()}")
        for constraint_key, value in self.constraints.items():
            if value is True:
                tokens.append(f"task:constraint:{constraint_key}")
            elif value:
                tokens.append(f"task:constraint:{constraint_key}:{str(value).lower()}")
        if self.active_subgoal:
            tokens.append(f"task:subgoal:{self.active_subgoal}")
        return tuple(tokens)


@dataclass(frozen=True, slots=True)
class GoalProgress:
    level: ProgressLevel
    status: GoalStatus
    evidence: tuple[str, ...] = ()
    satisfied_constraints: tuple[str, ...] = ()
    pending_constraints: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "status": self.status,
            "evidence": list(self.evidence),
            "satisfied_constraints": list(self.satisfied_constraints),
            "pending_constraints": list(self.pending_constraints),
        }
