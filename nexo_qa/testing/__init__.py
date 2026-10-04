"""P1 testing helpers — bind environments onto IntegratedRuntime without core branching."""

from __future__ import annotations

from typing import Any


def bind_world(runtime: Any, world: Any) -> Any:
    """Replace the runtime world after construction (adapter boundary, not PFC)."""
    runtime.world = world
    runtime.scheduler.config["world_state"] = world
    return runtime


def bind_task(runtime: Any, goal: Any, *, task_context: Any = None, world: Any = None) -> Any:
    """Wire declarative task goal into runtime (P4)."""
    from nexo_qa.goals.runtime import bind_task as _bind_task

    return _bind_task(runtime, goal=goal, task_context=task_context, world=world)


def bind_persona(runtime: Any, persona: Any, *, world: Any = None) -> Any:
    """Apply cognitive persona to runtime (P5)."""
    from nexo_qa.personas.runtime import bind_persona as _bind_persona

    return _bind_persona(runtime, persona=persona, world=world)
