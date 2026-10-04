"""Proxy de rutas estudio Flask — overlay integrado (Fase 13)."""

from __future__ import annotations

from typing import Any


STUDY_TRACKS = (
    "curriculum",
    "clinical_neurology",
    "biopsych",
    "infant_brain",
    "brain_facts",
    "anatomy_book",
)


def wrap_study_response(session: Any, response: dict[str, Any], *, track: str) -> dict[str, Any]:
    """Enriquece respuesta de estudio con bloque integrado advisory."""
    if session is None:
        return response
    if getattr(session.runtime.config, "flask_study_proxy_mode", "legacy") != "integrated":
        return response
    runtime = session.runtime
    from nexo.behavioral.memory_bridge import summarize_memory_bridge
    from nexo.behavioral.agent_loop_sync import summarize_agent_loop_sync

    out = dict(response)
    out["integrated_study"] = {
        "unified": True,
        "track": track,
        "profile": runtime.config.profile,
        "motor_authority": "integrated" if session.integrated_motor_primary else "legacy",
        "agent_loop_sync": summarize_agent_loop_sync(runtime),
        "memory_bridge": summarize_memory_bridge(runtime),
        "integrated_ticks": runtime.clock.tick,
    }
    return out


def curriculum_overlay(session: Any, curriculum_dict: dict[str, Any]) -> dict[str, Any]:
    if session is None:
        return curriculum_dict
    if getattr(session.runtime.config, "flask_study_proxy_mode", "legacy") != "integrated":
        return curriculum_dict
    out = dict(curriculum_dict)
    out["integrated"] = {
        "unified": True,
        "profile": session.runtime.config.profile,
        "flask_study_proxy_mode": getattr(session.runtime.config, "flask_study_proxy_mode", "legacy"),
    }
    return out
