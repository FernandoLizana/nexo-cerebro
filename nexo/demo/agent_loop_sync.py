"""Sincronización lite del agent_loop legacy tras tick integrado (Fase 13)."""

from __future__ import annotations

from typing import Any


def run_agent_loop_lite_sync(brain: Any) -> dict[str, Any]:
    """Post-proceso cognitivo legacy sin re-ejecutar motor/mundo.

    Actualiza afecto, lenguaje y compañera para que Flask refleje estado rico
    cuando el motor primario es integrado.
    """
    if not getattr(brain.lifecycle, "alive", True):
        return {"synced": False, "reason": "not_alive"}

    synced: list[str] = []
    all_events: list[dict[str, Any]] = []

    comp_events = brain.companion.tick(
        brain.world,
        room_temp=brain.world.room_temperature(),
        sleep_pressure=brain.brainstem.sleep_pressure,
        nexo_x=brain.world.agent_x,
        nexo_y=brain.world.agent_y,
        chemistry=brain.chemistry,
    )
    if comp_events:
        synced.append("companion")
        all_events.extend(comp_events)

    thought = brain.think(vision=getattr(brain, "_last_vision", None))
    synced.append("think")

    imagination = None
    if hasattr(brain, "imagination"):
        imagination = brain.imagination.advance_stream(
            brain, thought=thought, vision=getattr(brain, "_last_vision", None)
        )
        if imagination and imagination.get("active"):
            synced.append("imagination")

    last_ep = getattr(brain, "_last_ep", None) or {
        "hypothalamus": {
            "mood": brain.persona.mood,
            "energy": brain.hypothalamus.energy,
            "oxytocin": brain.hypothalamus.oxytocin,
        },
        "valence": brain.amygdala.valence,
        "arousal": brain.amygdala.arousal,
        "remembered": False,
        "motor": [],
        "label": brain.world.current_room(),
    }

    draft = brain._state_draft(
        last_ep,
        thought=thought.get("text"),
        event=all_events[-1] if all_events else None,
    )
    lctx = brain._language_context(
        ep=last_ep,
        draft=draft,
        mode="world",
        last_thought=thought.get("text"),
    )
    feel_text, feel_src = brain.language.describe_feelings(lctx)
    spoken, lang_src = brain._articulate(lctx)
    brain.persona.react(
        hypothalamus=last_ep["hypothalamus"],
        valence=last_ep["valence"],
        arousal=last_ep["arousal"],
        modality="world",
        label=str(last_ep.get("label", "world")),
        remembered=last_ep.get("remembered", False),
        motor=last_ep.get("motor", []),
        memory_hit=last_ep.get("memory") if last_ep.get("remembered") else None,
        reply=spoken,
    )
    synced.extend(["language", "persona"])

    loop = getattr(brain, "agent_loop", None)
    if loop is not None:
        loop.state.phase_trace.append("lite_sync")
        loop.state.phase_trace = loop.state.phase_trace[-12:]

    return {
        "synced": True,
        "phases": synced,
        "thought_len": len(str(thought.get("text", ""))),
        "feelings_len": len(feel_text or ""),
        "companion_events": len(comp_events),
        "imagination_active": bool(imagination and imagination.get("active")),
        "language_source": lang_src,
        "feelings_source": feel_src,
    }
