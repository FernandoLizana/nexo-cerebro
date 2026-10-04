"""Pila de sub-objetivos para RoomWorld."""

from __future__ import annotations

from dataclasses import dataclass, field

ROOM_PLANS: dict[str, list[tuple[str, str]]] = {
    "eat": [("eat", "food")],
    "flee": [("explore", "danger"), ("flee", "exit")],
    "rest": [("rest", "self")],
}


@dataclass
class GoalFrame:
    action: str
    target: str
    label: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"action": self.action, "target": self.target, "label": self.label}


@dataclass
class GoalStack:
    frames: list[GoalFrame] = field(default_factory=list)

    def depth(self) -> int:
        return len(self.frames)

    def peek_action(self) -> str | None:
        return self.frames[0].action if self.frames else None

    def push_plan(self, plan_key: str) -> bool:
        steps = ROOM_PLANS.get(plan_key)
        if not steps:
            return False
        self.frames = [
            GoalFrame(action=action, target=target, label=f"{plan_key}:{action}")
            for action, target in steps
        ]
        return True

    def advance_if_matched(self, executed_action: str) -> bool:
        if not self.frames:
            return False
        if executed_action == self.frames[0].action:
            self.frames.pop(0)
            return True
        return False

    def clear(self) -> None:
        self.frames.clear()

    def goal_labels(self) -> tuple[str, ...]:
        return tuple(f.label or f.action for f in self.frames)
