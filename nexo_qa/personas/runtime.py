"""Persona runtime — apply, bind, dynamic state process."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from nexo.core.events import CognitiveEvent
from nexo.core.module_protocol import ProcessContext
from nexo.core.process import BaseProcess
from nexo_qa.personas.mapping import apply_persona_to_config, build_persona_modifiers
from nexo_qa.personas.models import CognitivePersona, PersonaApplicationReport, PersonaState


@dataclass
class PersonaStateProcess(BaseProcess):
    """Track dynamic persona state — frustration, fatigue, stagnation."""

    process_id: str = "persona_state"
    period_ticks: int = 1
    priority: int = 62

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        persona: CognitivePersona | None = context.config.get("cognitive_persona")
        if persona is None:
            return []
        pstate: PersonaState = context.config.setdefault(
            "persona_state",
            PersonaState(current_confidence=persona.traits.semantic_confidence),
        )
        mods = context.config.get("persona_modifiers") or build_persona_modifiers(persona)
        tick = context.clock.tick
        t = context.clock.simulation_time
        events: list[CognitiveEvent] = []

        recent = context.state_store.event_log[-10:]
        for ev in recent:
            if ev.event_type == "goal.drift" and ev.tick >= tick - 1:
                pstate.ticks_without_progress += 1
            if ev.event_type == "goal.behavior_loop" and ev.tick >= tick - 1:
                pstate.repeated_action_count += 1
            if ev.event_type == "action.selected" and ev.tick >= tick - 1:
                action = str(ev.payload.get("action", ""))
                if pstate.last_action == action:
                    pstate.repeated_action_count += 1
                else:
                    pstate.repeated_action_count = max(0, pstate.repeated_action_count - 1)
                pstate.last_action = action

        world = context.config.get("world_state")
        if world is not None and getattr(world, "last_error", None):
            err = str(world.last_error)
            if err in ("ACTION_NO_LONGER_AVAILABLE", "POLICY_BLOCKED", "VALIDATION_ERROR"):
                pstate.current_frustration = min(
                    1.0,
                    pstate.current_frustration + 0.1 * (1.0 - float(mods.get("frustration_tolerance", 0.5))),
                )

        progress = context.config.get("goal_progress")
        patience = float(mods.get("patience", 0.5))
        tolerance = float(mods.get("frustration_tolerance", 0.5))
        fatigue_rate = float(mods.get("fatigue_rate_modifier", 1.0))

        if progress is not None:
            level = getattr(progress, "level", "none")
            if level in ("partial", "high", "complete"):
                pstate.ticks_without_progress = max(0, pstate.ticks_without_progress - 1)
            elif level == "none":
                pstate.ticks_without_progress += 1

        stagnation_limit = int(2 + patience * 5)
        if pstate.ticks_without_progress >= stagnation_limit:
            pstate.current_frustration = min(
                1.0,
                pstate.current_frustration + 0.07 * (1.0 - tolerance),
            )

        if pstate.repeated_action_count >= 3:
            pstate.current_frustration = min(
                1.0,
                pstate.current_frustration + 0.05 * (1.0 - tolerance),
            )

        pstate.current_frustration = max(0.0, pstate.current_frustration - 0.015 * max(0.2, tolerance))
        pstate.current_fatigue = min(
            1.0,
            pstate.current_fatigue + 0.0035 * fatigue_rate + 0.002 * pstate.current_frustration,
        )

        aff = context.state_store.state.affective
        context.config["persona_state"] = pstate
        events.append(
            CognitiveEvent(
                event_type="affect.updated",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "frustration": round(pstate.current_frustration, 4),
                    "valence": aff.valence - 0.05 * pstate.current_frustration,
                    "arousal": min(1.0, aff.arousal + 0.03 * pstate.current_frustration),
                    "uncertainty": aff.uncertainty,
                },
            )
        )
        events.append(
            CognitiveEvent(
                event_type="persona.state",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "persona_id": persona.persona_id,
                    "config_hash": persona.config_hash(),
                    "state": pstate.to_dict(),
                    "traits_immutable": True,
                },
            )
        )
        events.append(
            CognitiveEvent(
                event_type="homeostatic.fatigue_changed",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={"delta": 0.002 * fatigue_rate},
            )
        )
        return events


def apply_persona(
    runtime: Any,
    persona: CognitivePersona,
    *,
    world: Any | None = None,
) -> PersonaApplicationReport:
    """Single auditable entry point for persona → NEXO mechanistic config."""
    config = runtime.scheduler.config
    report = apply_persona_to_config(config, persona)
    if world is not None:
        runtime.world = world
        config["world_state"] = world
    w = config.get("world_state")
    pov = config.get("persona_perception_override")
    if w is not None and pov is not None and hasattr(w, "config"):
        w.config = replace(w.config, perception=pov)
    if not config.get("_persona_process_registered"):
        runtime.scheduler.register(PersonaStateProcess())
        config["_persona_process_registered"] = True
    return report


def bind_persona(
    runtime: Any,
    persona: CognitivePersona,
    *,
    world: Any | None = None,
) -> Any:
    """Apply persona to an existing runtime (P5 testing helper)."""
    apply_persona(runtime, persona, world=world)
    return runtime
