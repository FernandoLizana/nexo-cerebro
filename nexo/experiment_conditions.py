"""Configuraciones experimentales versionadas con listas explícitas de flags."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields, replace
from enum import Enum
from typing import Any

from brain.experiment_flags import AblationFlags

CONFIG_VERSION = 1
CONDITION_FAMILY_BASELINE = "baseline_legacy"
CONDITION_FAMILY_ROADMAP100 = "roadmap100_v1"

# Lista explícita v1 — NO auto-habilitar todos los enable_*.
ROADMAP100_V1_ENABLED_FLAGS: frozenset[str] = frozenset({
    "enable_td_reward",
    "enable_circadian",
    "enable_limited_wm",
    "enable_attention_budget",
    "enable_selective_sleep",
    "enable_grounding",
    "enable_learned_schemas",
    "enable_lifecycle_plasticity",
    "enable_lobe_virtual_inject",
    "enable_laminar_columns",
    "enable_interneuron_subtypes",
    "enable_vascular_coupling",
    "enable_decompression_prefetch",
    "enable_rhythm_pac",
    "enable_sleep_spindles",
    "enable_scn_jetlag",
    "enable_regional_lobe_bus",
    "enable_temporal_prediction",
    "enable_advanced_sensory",
    "enable_saccadic_vision",
    "enable_superior_colliculus",
    "enable_referred_pain",
    "enable_cardiac_interoception",
    "enable_executive_cognition",
    "enable_dual_task_metrics",
    "enable_stroop_inhibition",
    "enable_set_shifting",
    "enable_dmn_replay",
    "enable_metacognition_calibration",
    "enable_tower_goals",
    "enable_imagination_motor",
    "enable_memory_dynamics",
    "enable_rich_episodic_context",
    "enable_forgetting_curve",
    "enable_memory_interference",
    "enable_source_confusion",
    "enable_flashbulb_memory",
    "enable_autobiographical_timeline",
    "enable_reward_learning",
    "enable_rpe_surprise_coupling",
    "enable_causal_transfer",
    "enable_latent_affordance",
    "enable_schema_extinction",
    "enable_model_based_deliberation",
    "enable_metaplasticity_bcm",
    "enable_affect_dynamics",
    "enable_receptor_panel",
    "enable_hpa_axis",
    "enable_emotion_regulation",
    "enable_empathy_contagion",
    "enable_attachment_style",
    "enable_social_shame",
    "enable_hedonic_wanting",
    "enable_goal_frustration",
    "enable_persistent_mood",
    "enable_social_turns",
    "enable_language_dynamics",
    "enable_neural_language_default",
    "enable_curriculum_verbalization",
    "enable_grounding_chat",
    "enable_prosody",
    "enable_inner_outer_speech",
    "enable_bilingual_codeswitch",
    "enable_language_tutor_rag",
    "enable_motor_dynamics",
    "enable_cerebellum_adaptation",
    "enable_basal_habituation",
    "enable_muscular_fatigue",
    "enable_world_depth",
    "enable_somatic_passive",
    "enable_food_cycle",
    "enable_desk_study_deterministic",
    "enable_lifecycle_dynamics",
    "enable_full_sleep_architecture",
    "enable_nocturnal_study",
    "enable_lifecycle_stages",
    "enable_puberty_hormones",
    "enable_cognitive_aging",
    "enable_validation_dynamics",
    "enable_observatory_hud",
    "enable_continuous_motor",
    "enable_multimodal_delays",
    "enable_affordance_learning",
    "enable_neural_telemetry",
    "enable_counterfactual",
    "enable_sleep_study",
    "enable_sleep_web",
})

ROADMAP100_V1_EXCLUDED_FLAGS: frozenset[str] = frozenset({
    "enable_broca_aphasia",
    "enable_wernicke_aphasia",
    "enable_verify",
    "enable_goal_stack",
    "enable_connectome_scaffold",
    "enable_consciousness",
})


def find_unclassified_enable_flags() -> set[str]:
    all_enable = {f.name for f in fields(AblationFlags) if f.name.startswith("enable_")}
    classified = ROADMAP100_V1_ENABLED_FLAGS | ROADMAP100_V1_EXCLUDED_FLAGS
    return all_enable - classified


@dataclass(frozen=True)
class ExperimentCondition:
    condition_id: str
    condition_family: str
    version: int
    description: str
    parent_condition: str | None
    flags: AblationFlags

    def flags_dict(self) -> dict[str, Any]:
        return asdict(self.flags)

    def config_hash(self) -> str:
        payload = {
            "condition_id": self.condition_id,
            "condition_family": self.condition_family,
            "version": self.version,
            "flags": self.flags_dict(),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def to_metadata(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "condition_family": self.condition_family,
            "version": self.version,
            "description": self.description,
            "parent_condition": self.parent_condition,
            "config_hash": self.config_hash(),
            "flags": self.flags_dict(),
        }


def _apply_flag_set(base: AblationFlags, enabled: frozenset[str]) -> AblationFlags:
    kwargs = {f.name: getattr(base, f.name) for f in fields(AblationFlags)}
    for name in enabled:
        kwargs[name] = True
    return AblationFlags(**kwargs)  # type: ignore[arg-type]


def baseline_legacy_flags() -> AblationFlags:
    return AblationFlags()


def roadmap100_full_v1_flags() -> AblationFlags:
    return _apply_flag_set(AblationFlags(), ROADMAP100_V1_ENABLED_FLAGS)


def roadmap100_safe_v1_flags() -> AblationFlags:
    return replace(
        AblationFlags(),
        enable_memory_dynamics=True,
        enable_executive_cognition=True,
        enable_validation_dynamics=True,
        enable_observatory_hud=True,
        enable_limited_wm=True,
        enable_attention_budget=True,
        enable_neural_telemetry=True,
    )


def roadmap100_no_binding_v1_flags() -> AblationFlags:
    return replace(roadmap100_full_v1_flags(), bind_deliberation=False)


def roadmap100_no_pfc_v1_flags() -> AblationFlags:
    return replace(roadmap100_full_v1_flags(), force_limbic_winner=True)


def roadmap100_no_hippocampus_v1_flags() -> AblationFlags:
    return replace(roadmap100_full_v1_flags(), disable_hippocampus=True)


def roadmap100_no_affect_v1_flags() -> AblationFlags:
    return replace(roadmap100_full_v1_flags(), disable_affect=True)


def roadmap100_no_consciousness_v1_flags() -> AblationFlags:
    return replace(roadmap100_full_v1_flags(), enable_consciousness=False)


# Familia legacy E1 (baseline OFF)
def legacy_no_binding_flags() -> AblationFlags:
    return replace(baseline_legacy_flags(), bind_deliberation=False)


def legacy_no_pfc_flags() -> AblationFlags:
    return replace(baseline_legacy_flags(), force_limbic_winner=True)


def legacy_no_hippocampus_flags() -> AblationFlags:
    return replace(baseline_legacy_flags(), disable_hippocampus=True)


def legacy_no_affect_flags() -> AblationFlags:
    return replace(baseline_legacy_flags(), disable_affect=True)


def legacy_no_consciousness_flags() -> AblationFlags:
    return replace(baseline_legacy_flags(), enable_consciousness=False)


# Aliases retrocompatibles
baseline_flags = baseline_legacy_flags
roadmap100_full_flags = roadmap100_full_v1_flags
roadmap100_safe_flags = roadmap100_safe_v1_flags
no_binding_flags = legacy_no_binding_flags
no_pfc_flags = legacy_no_pfc_flags


def _cond(
    cid: str,
    family: str,
    desc: str,
    flags: AblationFlags,
    parent: str | None = None,
) -> ExperimentCondition:
    return ExperimentCondition(
        condition_id=cid,
        condition_family=family,
        version=CONFIG_VERSION,
        description=desc,
        parent_condition=parent,
        flags=flags,
    )


_BUILDERS: dict[str, Any] = {
    "baseline_legacy": lambda: _cond("baseline_legacy", CONDITION_FAMILY_BASELINE, "Paper histórico E1–E3", baseline_legacy_flags()),
    "roadmap100_full_v1": lambda: _cond("roadmap100_full_v1", CONDITION_FAMILY_ROADMAP100, "Roadmap100 v1 completo", roadmap100_full_v1_flags()),
    "roadmap100_safe_v1": lambda: _cond("roadmap100_safe_v1", CONDITION_FAMILY_ROADMAP100, "Roadmap100 v1 CI", roadmap100_safe_v1_flags(), "roadmap100_full_v1"),
    "roadmap100_no_binding_v1": lambda: _cond("roadmap100_no_binding_v1", CONDITION_FAMILY_ROADMAP100, "Roadmap100 sin bind", roadmap100_no_binding_v1_flags(), "roadmap100_full_v1"),
    "roadmap100_no_pfc_v1": lambda: _cond("roadmap100_no_pfc_v1", CONDITION_FAMILY_ROADMAP100, "Roadmap100 sin PFC", roadmap100_no_pfc_v1_flags(), "roadmap100_full_v1"),
    "roadmap100_no_hippocampus_v1": lambda: _cond("roadmap100_no_hippocampus_v1", CONDITION_FAMILY_ROADMAP100, "Roadmap100 sin hippo", roadmap100_no_hippocampus_v1_flags(), "roadmap100_full_v1"),
    "roadmap100_no_affect_v1": lambda: _cond("roadmap100_no_affect_v1", CONDITION_FAMILY_ROADMAP100, "Roadmap100 sin afecto", roadmap100_no_affect_v1_flags(), "roadmap100_full_v1"),
    "roadmap100_no_consciousness_v1": lambda: _cond("roadmap100_no_consciousness_v1", CONDITION_FAMILY_ROADMAP100, "Roadmap100 sin consciencia", roadmap100_no_consciousness_v1_flags(), "roadmap100_full_v1"),
    "legacy_no_binding": lambda: _cond("legacy_no_binding", CONDITION_FAMILY_BASELINE, "Legacy nobind", legacy_no_binding_flags(), "baseline_legacy"),
    "legacy_no_pfc": lambda: _cond("legacy_no_pfc", CONDITION_FAMILY_BASELINE, "Legacy nopfc", legacy_no_pfc_flags(), "baseline_legacy"),
    # aliases
    "baseline": lambda: get_condition("baseline_legacy"),
    "roadmap100_full": lambda: get_condition("roadmap100_full_v1"),
    "full": lambda: get_condition("baseline_legacy"),
    "nobind": lambda: get_condition("legacy_no_binding"),
    "nopfc": lambda: get_condition("legacy_no_pfc"),
}


def get_condition(condition_id: str) -> ExperimentCondition:
    key = condition_id.strip().lower().replace("-", "_")
    if key not in _BUILDERS:
        known = ", ".join(sorted(_BUILDERS))
        raise ValueError(f"Condición desconocida: {condition_id!r}. Conocidas: {known}")
    return _BUILDERS[key]()
