"""Capture raw cognitive run trace from IntegratedRuntime."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from nexo_qa.analysis.models import RawRunTrace, _new_id


def _serialize_event(ev: Any) -> dict[str, Any]:
    return {
        "event_type": ev.event_type,
        "source": ev.source,
        "tick": ev.tick,
        "simulation_time": ev.simulation_time,
        "trace_id": ev.trace_id,
        "payload": dict(ev.payload or {}),
        "target": ev.target,
        "causal_parent": ev.causal_parent,
    }


def capture_run_trace(runtime: Any, *, world: Any | None = None, run_id: str | None = None) -> RawRunTrace:
    """Snapshot runtime event log + world trace for offline QA analysis."""
    config = runtime.scheduler.config
    goal = config.get("task_goal")
    persona = config.get("cognitive_persona")
    progress = config.get("goal_progress")
    pstate = config.get("persona_state")
    w = world or config.get("world_state") or getattr(runtime, "world", None)
    meta: dict[str, Any] = {
        "goal": goal.to_dict() if goal is not None and hasattr(goal, "to_dict") else None,
        "goal_id": getattr(goal, "goal_id", None),
        "goal_description": getattr(goal, "description", ""),
        "persona_id": getattr(persona, "persona_id", None) if persona else None,
        "persona_traits": persona.traits.to_dict() if persona and hasattr(persona, "traits") else None,
        "final_progress": progress.to_dict() if progress is not None and hasattr(progress, "to_dict") else None,
        "persona_state": pstate.to_dict() if pstate is not None and hasattr(pstate, "to_dict") else None,
        "action_history": list(getattr(w, "action_history", []) or []),
        "action_salience": dict(config.get("action_salience") or {}),
        "goal_relevance": dict(config.get("goal_relevance") or {}),
        "deliberation_available": config.get("deliberation_result") is not None,
    }
    world_trace = list(getattr(w, "trace_log", []) or [])
    rid = run_id or _new_id("run")
    return RawRunTrace(
        run_id=rid,
        seed=int(getattr(runtime.config, "seed", 0)),
        ticks=int(runtime.clock.tick),
        events=[_serialize_event(ev) for ev in runtime.state_store.event_log],
        world_trace=world_trace,
        metadata=meta,
    )
