"""
Pila de sub-objetivos PFC — planes multi-tick sin planificador LLM.

Cuando la deliberación elige un esquema con target (nevera, cama, …),
empuja [navigate, interact] en WM; se consume al completar interacción.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .deliberation import ACTION_SCHEMAS

# Planes multi-paso (tower task) — navigate → interact → acción
TOWER_PLANS: dict[str, list[tuple[str, str, str]]] = {
    "study": [
        ("navigate", "escritorio", "Ir al escritorio"),
        ("interact", "desk", "Sentarse a estudiar"),
        ("study", "desk", "Leer capítulo"),
    ],
    "research": [
        ("navigate", "escritorio", "Ir al escritorio"),
        ("interact", "desk", "Abrir monitor"),
        ("research", "desk", "Buscar información"),
    ],
    "cook": [
        ("navigate", "cocina", "Ir a cocina"),
        ("interact", "stove", "Encender cocina"),
        ("cook", "stove", "Preparar comida"),
    ],
    "eat_cooked": [
        ("navigate", "cocina", "Ir a nevera"),
        ("interact", "fridge", "Abrir nevera"),
        ("eat", "fridge", "Comer"),
    ],
    "harvest": [
        ("navigate", "jardín", "Ir al jardín"),
        ("interact", "crop", "Cosechar"),
        ("harvest", "crop", "Recoger cultivo"),
    ],
}


@dataclass
class GoalFrame:
    choice_key: str
    label: str
    target: str
    phase: str  # navigate | interact

    def to_dict(self) -> dict[str, Any]:
        return {
            "choice_key": self.choice_key,
            "label": self.label,
            "target": self.target,
            "phase": self.phase,
        }


@dataclass
class GoalStack:
    frames: list[GoalFrame] = field(default_factory=list)
    _stall_ticks: int = field(default=0, init=False, repr=False)

    def depth(self) -> int:
        return len(self.frames)

    def peek(self) -> GoalFrame | None:
        return self.frames[0] if self.frames else None

    def push_from_deliberation(self, choice_key: str, choice_label: str, brain=None) -> bool:
        from .experiment_flags import get_flags

        if brain is not None and get_flags(brain).enable_tower_goals:
            if choice_key in TOWER_PLANS:
                self.frames.clear()
                for phase, target, lbl in TOWER_PLANS[choice_key]:
                    self.frames.append(
                        GoalFrame(
                            choice_key=choice_key,
                            label=lbl or choice_label,
                            target=target,
                            phase=phase,
                        )
                    )
                return True
        if brain is not None:
            from .learned_schemas import all_action_schemas

            pool = all_action_schemas(brain)
        else:
            pool = ACTION_SCHEMAS
        schema = next((s for s in pool if s["key"] == choice_key), None)
        if not schema or not schema.get("target"):
            return False
        target = schema["target"]
        if self.frames and self.frames[-1].choice_key == choice_key:
            return False
        self.frames.clear()
        self.frames.append(
            GoalFrame(
                choice_key=choice_key,
                label=choice_label,
                target=target,
                phase="navigate",
            )
        )
        self.frames.append(
            GoalFrame(
                choice_key=choice_key,
                label=choice_label,
                target=target,
                phase="interact",
            )
        )
        return True

    def on_interact_complete(self, target_kind: str) -> bool:
        """Pop cuando el agente interactúa con el mueble objetivo."""
        if not self.frames:
            return False
        top = self.frames[0]
        if top.target and top.target != target_kind:
            return False
        while self.frames and self.frames[0].target == target_kind:
            self.frames.pop(0)
        return True

    def sync_working_memory(self, brain) -> None:
        top = self.peek()
        if top:
            brain.working_memory.set_goal(f"{top.label} ({top.phase})")
        elif brain.deliberation.last.choice:
            brain.working_memory.set_goal(brain.deliberation.last.choice)

    def tick_stall(self, *, progressed: bool) -> int:
        if progressed:
            self._stall_ticks = 0
        elif self.frames:
            self._stall_ticks += 1
        else:
            self._stall_ticks = 0
        return self._stall_ticks

    def to_dict(self) -> dict[str, Any]:
        return {
            "depth": self.depth(),
            "stall_ticks": self._stall_ticks,
            "frames": [f.to_dict() for f in self.frames[:8]],
            "tower_mode": any(f.phase not in ("navigate", "interact") for f in self.frames),
        }
