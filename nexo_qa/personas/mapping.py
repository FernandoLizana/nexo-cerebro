"""Mechanistic mapping — persona traits → NEXO parameters."""

from __future__ import annotations

from typing import Any

from nexo_qa.personas.models import CognitivePersona, MechanisticMappingEntry, PersonaApplicationReport, PersonaState
from nexo_qa.personas.validation import validate_traits

MECHANISTIC_MAP: tuple[MechanisticMappingEntry, ...] = (
    MechanisticMappingEntry("working_memory_capacity", "WorkingMemoryBuffer", "capacity", "limits active items retained"),
    MechanisticMappingEntry("attention_persistence", "PerceptionConfig", "max_focal_percepts", "focal attention slots"),
    MechanisticMappingEntry("visual_search_efficiency", "PerceptionConfig", "max_attended_percepts", "perceptual attention budget"),
    MechanisticMappingEntry("distractibility", "EnhancedBasalGangliaProcess", "persona_modifiers.distractibility", "salience-without-goal boost"),
    MechanisticMappingEntry("risk_aversion", "EnhancedBasalGangliaProcess", "persona_modifiers.risk_aversion", "penalizes high-risk actions"),
    MechanisticMappingEntry("exploration_tendency", "EnhancedBasalGangliaProcess", "persona_modifiers.exploration_tendency", "boosts scroll/navigate"),
    MechanisticMappingEntry("impulsivity", "PrefrontalDeliberator", "pfc_inhibition_strength", "reduces PFC deliberation weight"),
    MechanisticMappingEntry("digital_literacy", "PrefrontalDeliberator", "persona_modifiers.digital_literacy", "scales goal relevance"),
    MechanisticMappingEntry("semantic_confidence", "PrefrontalDeliberator", "persona_modifiers.semantic_confidence", "confidence in semantic inference"),
    MechanisticMappingEntry("patience", "PersonaStateProcess", "persona_modifiers.patience", "progress stagnation tolerance"),
    MechanisticMappingEntry("frustration_tolerance", "PersonaStateProcess", "persona_state.current_frustration", "failure response threshold"),
    MechanisticMappingEntry("initial_fatigue", "HomeostaticState", "fatigue", "starting fatigue level"),
    MechanisticMappingEntry("learning_rate_modifier", "TDRewardSystem", "learning_rate_scale", "TD learning scale"),
    MechanisticMappingEntry("metacognitive_sensitivity", "MetacognitiveMonitor", "persona_modifiers.metacognitive_sensitivity", "doubt/reconsideration gain"),
    MechanisticMappingEntry("fatigue_rate_modifier", "PersonaStateProcess", "persona_modifiers.fatigue_rate_modifier", "fatigue accumulation rate"),
)


def build_persona_modifiers(persona: CognitivePersona) -> dict[str, float]:
    t = persona.traits
    return {
        "distractibility": t.distractibility,
        "risk_aversion": t.risk_aversion,
        "exploration_tendency": t.exploration_tendency,
        "digital_literacy": t.digital_literacy,
        "semantic_confidence": t.semantic_confidence,
        "patience": t.patience,
        "frustration_tolerance": t.frustration_tolerance,
        "impulsivity": t.impulsivity,
        "metacognitive_sensitivity": t.metacognitive_sensitivity,
        "fatigue_rate_modifier": t.fatigue_rate_modifier,
        "learning_rate_modifier": t.learning_rate_modifier,
        "attention_persistence": t.attention_persistence,
    }


def apply_persona_to_config(config: dict[str, Any], persona: CognitivePersona) -> PersonaApplicationReport:
    from nexo_qa.perception.config import PerceptionConfig

    errors = validate_traits(persona.traits.to_dict())
    if errors:
        raise ValueError("; ".join(errors))
    report = PersonaApplicationReport(persona_id=persona.persona_id, config_hash=persona.config_hash())
    t = persona.traits

    buf = config.setdefault("wm_buffer", None)
    if buf is not None:
        buf.capacity = max(1, min(12, t.working_memory_capacity))
        report.add(
            trait="working_memory_capacity",
            module="WorkingMemoryBuffer",
            parameter="capacity",
            requested=t.working_memory_capacity,
            effective=buf.capacity,
            effect="limits WM items",
        )

    deliberator = config.setdefault("prefrontal_deliberator", None)
    if deliberator is not None:
        requested_inhibition = max(0.15, min(0.85, 0.55 - (t.impulsivity - 0.5) * 0.35))
        deliberator.pfc_inhibition_strength = requested_inhibition
        report.add(
            trait="impulsivity",
            module="PrefrontalDeliberator",
            parameter="pfc_inhibition_strength",
            requested=t.impulsivity,
            effective=deliberator.pfc_inhibition_strength,
            effect="PFC vs limbic balance",
        )

    perception: PerceptionConfig | None = config.get("persona_perception_override")
    if perception is None:
        perception = PerceptionConfig()
    focal = max(2, min(8, int(4 + (t.attention_persistence - 0.5) * 4)))
    attended = max(4, min(16, int(8 + (t.visual_search_efficiency - 0.5) * 8)))
    perception = PerceptionConfig(
        mode=perception.mode,
        max_focal_percepts=focal,
        max_attended_percepts=attended,
        max_percepts=perception.max_percepts,
    )
    config["persona_perception_override"] = perception
    report.add(
        trait="attention_persistence",
        module="PerceptionConfig",
        parameter="max_focal_percepts",
        requested=t.attention_persistence,
        effective=focal,
        effect="focal slots",
    )
    report.add(
        trait="visual_search_efficiency",
        module="PerceptionConfig",
        parameter="max_attended_percepts",
        requested=t.visual_search_efficiency,
        effective=attended,
        effect="attention budget",
    )

    td = config.get("td_system")
    if td is not None and hasattr(td, "alpha"):
        scale = max(0.1, min(3.0, t.learning_rate_modifier))
        if hasattr(td, "learning_rate_scale"):
            td.learning_rate_scale = scale
        report.add(
            trait="learning_rate_modifier",
            module="TDRewardSystem",
            parameter="learning_rate_scale",
            requested=t.learning_rate_modifier,
            effective=scale,
            effect="TD update scale",
        )

    hctrl = config.get("homeostatic_controller")
    if hctrl is not None and t.initial_fatigue > 0:
        hctrl.body.fatigue = max(0.0, min(1.0, t.initial_fatigue))
        report.add(
            trait="initial_fatigue",
            module="HomeostaticState",
            parameter="fatigue",
            requested=t.initial_fatigue,
            effective=hctrl.body.fatigue,
            effect="starting fatigue",
        )

    config["cognitive_persona"] = persona
    config["persona_modifiers"] = build_persona_modifiers(persona)
    config["persona_state"] = PersonaState(
        current_frustration=0.0,
        current_fatigue=t.initial_fatigue,
        current_confidence=t.semantic_confidence,
    )
    config["persona_application_report"] = report
    return report
