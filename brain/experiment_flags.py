"""
Flags centralizados para ablaciones reproducibles (paper / experiments/).

Se adjuntan a ``InfantApeBrain.experiment_flags``; el runner headless los configura
sin esparcir ``if`` por ``mind.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .mind import InfantApeBrain


@dataclass(frozen=True)
class AblationFlags:
    bind_deliberation: bool = True
    force_limbic_winner: bool = False
    disable_hippocampus: bool = False
    disable_affect: bool = False
    enable_verify: bool = True
    enable_goal_stack: bool = True
    enable_connectome_scaffold: bool = False
    enable_consciousness: bool = True
    # TD dopamina predictiva: OFF en batch paper (E1–E3); ON en demo vía app.py / env.
    enable_td_reward: bool = False
    # Ritmo circadiano de cortisol (sesgo suave; no fuerza acciones).
    enable_circadian: bool = False
    # WM con capacidad/interferencia (Miller ~7); OFF en paper.
    enable_limited_wm: bool = False
    # Atención competitiva top-down/bottom-up con presupuesto; OFF en paper.
    enable_attention_budget: bool = False
    # Sueño selectivo (prioriza |valence|); OFF en paper E3; E4 lo activa explícito.
    enable_selective_sleep: bool = False
    # Lenguaje grounded (palabras→drives/sensory); OFF en paper; ON en demo.
    enable_grounding: bool = False
    # Schemas motores aprendidos por consolidación; OFF en paper.
    enable_learned_schemas: bool = False
    # Plasticidad / inhibición PFC según etapa vital; OFF en paper.
    enable_lifecycle_plasticity: bool = False
    # Inyección virtual → columnas lobulares (50k / escala); ON en demo por defecto.
    enable_lobe_virtual_inject: bool = False
    # Columnas laminares L4/L2/3/L5/L6 en corteza asociativa.
    enable_laminar_columns: bool = False
    # Interneuronas PV/SST/VIP en lugar de pool único.
    enable_interneuron_subtypes: bool = False
    # Lecho vascular (glucosa, O2, BBB) acoplado a ganancia sináptica.
    enable_vascular_coupling: bool = False
    # Prefetch predictivo de ensambles/scaffold cada tick.
    enable_decompression_prefetch: bool = False
    # Bloque B: θ–γ PAC, δ/spindles, β pre-motor, sincronía callosal.
    enable_rhythm_pac: bool = False
    enable_sleep_spindles: bool = False
    # SCN + jet lag (reloj interno vs luz ambiental).
    enable_scn_jetlag: bool = False
    # Bus regional con latencias interlobulares (materia blanca).
    enable_regional_lobe_bus: bool = False
    # Predicción temporal de hambre/sed/sueño (sesga WM/drives).
    enable_temporal_prediction: bool = False
    # Bloque C: percepción sensorial ampliada (audición, gusto, vestibular, SC).
    enable_advanced_sensory: bool = False
    enable_saccadic_vision: bool = False
    enable_superior_colliculus: bool = False
    enable_referred_pain: bool = False
    enable_cardiac_interoception: bool = False
    # Bloque D: cognición ejecutiva, DMN, Stroop, tower goals, metacognición.
    enable_executive_cognition: bool = False
    enable_dual_task_metrics: bool = False
    enable_stroop_inhibition: bool = False
    enable_set_shifting: bool = False
    enable_dmn_replay: bool = False
    enable_metacognition_calibration: bool = False
    enable_tower_goals: bool = False
    enable_imagination_motor: bool = False
    # Bloque E: memoria dinámica, olvido, flashbulb, autobiografía.
    enable_memory_dynamics: bool = False
    enable_rich_episodic_context: bool = False
    enable_forgetting_curve: bool = False
    enable_memory_interference: bool = False
    enable_source_confusion: bool = False
    enable_flashbulb_memory: bool = False
    enable_autobiographical_timeline: bool = False
    # Bloque F: aprendizaje por recompensa, causalidad, metaplasticidad.
    enable_reward_learning: bool = False
    enable_rpe_surprise_coupling: bool = False
    enable_causal_transfer: bool = False
    enable_latent_affordance: bool = False
    enable_schema_extinction: bool = False
    enable_model_based_deliberation: bool = False
    enable_metaplasticity_bcm: bool = False
    # Bloque G: emoción, afecto y vínculo social.
    enable_affect_dynamics: bool = False
    enable_receptor_panel: bool = False
    enable_hpa_axis: bool = False
    enable_emotion_regulation: bool = False
    enable_empathy_contagion: bool = False
    enable_attachment_style: bool = False
    enable_social_shame: bool = False
    enable_hedonic_wanting: bool = False
    enable_goal_frustration: bool = False
    enable_persistent_mood: bool = False
    enable_social_turns: bool = False
    # Bloque H: lenguaje y comunicación.
    enable_language_dynamics: bool = False
    enable_neural_language_default: bool = False
    enable_curriculum_verbalization: bool = False
    enable_grounding_chat: bool = False
    enable_prosody: bool = False
    enable_inner_outer_speech: bool = False
    enable_broca_aphasia: bool = False
    enable_wernicke_aphasia: bool = False
    enable_bilingual_codeswitch: bool = False
    enable_language_tutor_rag: bool = False
    # Bloque I: motor, cuerpo y mundo encarnado.
    enable_motor_dynamics: bool = False
    enable_cerebellum_adaptation: bool = False
    enable_basal_habituation: bool = False
    enable_muscular_fatigue: bool = False
    enable_world_depth: bool = False
    enable_somatic_passive: bool = False
    enable_food_cycle: bool = False
    enable_desk_study_deterministic: bool = False
    # Bloque J: sueño, desarrollo y ciclo vital.
    enable_lifecycle_dynamics: bool = False
    enable_full_sleep_architecture: bool = False
    enable_nocturnal_study: bool = False
    enable_lifecycle_stages: bool = False
    enable_puberty_hormones: bool = False
    enable_cognitive_aging: bool = False
    # Bloque K: validación, observatorio y guardrails.
    enable_validation_dynamics: bool = False
    enable_observatory_hud: bool = False
    # Política motora continua (priors); OFF en paper.
    enable_continuous_motor: bool = False
    # Latencias multimodales vision/audition/proprio; OFF en paper.
    enable_multimodal_delays: bool = False
    # Level 2: objeto+interacción→consecuencia; evidencia acotada para PFC.
    enable_affordance_learning: bool = False
    # Level 2.2: telemetría cognitiva compacta por tick (API/Arena).
    enable_neural_telemetry: bool = False
    # Level 2.3: predicciones contrafactuales acotadas (no eligen acción).
    enable_counterfactual: bool = False
    # Estudio autónomo durante sueño REM / background nocturno.
    enable_sleep_study: bool = False
    # Búsqueda web durante estudio nocturno (HTTP; no abre navegador real).
    enable_sleep_web: bool = False
    verify_conflict_threshold: float = 0.35
    rechoice_penalty: float = 0.15


def get_flags(brain: InfantApeBrain) -> AblationFlags:
    return getattr(brain, "experiment_flags", AblationFlags())


def apply_condition(name: str) -> AblationFlags:
    """Legacy E1 conditions. Prefer ``nexo.experiment_conditions.get_condition``.

    Note: ``full`` maps to historical baseline (roadmap dynamics OFF), NOT roadmap100_full.
    """
    key = name.strip().lower().replace("-", "").replace("_", "")
    table: dict[str, AblationFlags] = {
        "full": AblationFlags(),
        "nobind": replace(AblationFlags(), bind_deliberation=False),
        "nopfc": replace(AblationFlags(), force_limbic_winner=True),
        "nohippo": replace(AblationFlags(), disable_hippocampus=True),
        "noaffect": replace(AblationFlags(), disable_affect=True),
        "noverify": replace(AblationFlags(), enable_verify=False),
        "nogoalstack": replace(AblationFlags(), enable_goal_stack=False),
        "noscaffold": replace(AblationFlags(), enable_connectome_scaffold=False),
        "scaffold": replace(AblationFlags(), enable_connectome_scaffold=True),
        "noconscious": replace(AblationFlags(), enable_consciousness=False),
        "notd": replace(AblationFlags(), enable_td_reward=False),
        "td": replace(AblationFlags(), enable_td_reward=True),
        "nowm": replace(AblationFlags(), enable_limited_wm=False),
        "noattention": replace(AblationFlags(), enable_attention_budget=False),
    }
    if key not in table:
        raise ValueError(f"Condición desconocida: {name!r}. Usa: {', '.join(table)}")
    return table[key]


CONDITION_NAMES: tuple[str, ...] = ("full", "nobind", "nopfc", "nohippo", "noaffect", "noconscious")


def resolve_demo_flags() -> AblationFlags:
    """Flags para Flask demo: TD + circadiano + WM + atención ON; paper batch sigue OFF."""
    import os

    def _on(name: str, default: str = "1") -> bool:
        return os.environ.get(name, default).strip().lower() not in ("0", "false", "off", "no")

    return replace(
        AblationFlags(),
        enable_td_reward=_on("CEREBRO_TD"),
        enable_circadian=_on("CEREBRO_CIRCADIAN"),
        enable_limited_wm=_on("CEREBRO_LIMITED_WM"),
        enable_attention_budget=_on("CEREBRO_ATTENTION_BUDGET"),
        enable_grounding=_on("CEREBRO_GROUNDING"),
        enable_learned_schemas=_on("CEREBRO_LEARNED_SCHEMAS"),
        enable_lifecycle_plasticity=_on("CEREBRO_LIFECYCLE_PLASTICITY"),
        enable_lobe_virtual_inject=_on("CEREBRO_LOBE_VIRTUAL"),
        enable_laminar_columns=_on("CEREBRO_LAMINAR"),
        enable_interneuron_subtypes=_on("CEREBRO_INH_SUBTYPES"),
        enable_vascular_coupling=_on("CEREBRO_VASCULAR"),
        enable_decompression_prefetch=_on("CEREBRO_DECOMPRESS_PREFETCH"),
        enable_rhythm_pac=_on("CEREBRO_RHYTHM_PAC"),
        enable_sleep_spindles=_on("CEREBRO_SLEEP_SPINDLES"),
        enable_scn_jetlag=_on("CEREBRO_SCN"),
        enable_regional_lobe_bus=_on("CEREBRO_LOBE_BUS"),
        enable_temporal_prediction=_on("CEREBRO_TEMPORAL_PRED"),
        enable_advanced_sensory=_on("CEREBRO_ADVANCED_SENSORY"),
        enable_saccadic_vision=_on("CEREBRO_SACCADIC"),
        enable_superior_colliculus=_on("CEREBRO_SUPERIOR_COLLICULUS"),
        enable_referred_pain=_on("CEREBRO_REFERRED_PAIN"),
        enable_cardiac_interoception=_on("CEREBRO_CARDIAC"),
        enable_executive_cognition=_on("CEREBRO_EXECUTIVE"),
        enable_dual_task_metrics=_on("CEREBRO_DUAL_TASK"),
        enable_stroop_inhibition=_on("CEREBRO_STROOP"),
        enable_set_shifting=_on("CEREBRO_SET_SHIFT"),
        enable_dmn_replay=_on("CEREBRO_DMN"),
        enable_metacognition_calibration=_on("CEREBRO_METACOG"),
        enable_tower_goals=_on("CEREBRO_TOWER_GOALS"),
        enable_imagination_motor=_on("CEREBRO_IMAG_MOTOR"),
        enable_memory_dynamics=_on("CEREBRO_MEMORY_DYNAMICS"),
        enable_rich_episodic_context=_on("CEREBRO_RICH_EPISODIC"),
        enable_forgetting_curve=_on("CEREBRO_FORGETTING"),
        enable_memory_interference=_on("CEREBRO_INTERFERENCE"),
        enable_source_confusion=_on("CEREBRO_SOURCE_CONFUSION"),
        enable_flashbulb_memory=_on("CEREBRO_FLASHBULB"),
        enable_autobiographical_timeline=_on("CEREBRO_AUTOBIOGRAPHY"),
        enable_selective_sleep=_on("CEREBRO_SELECTIVE_SLEEP"),
        enable_counterfactual=_on("CEREBRO_COUNTERFACTUAL"),
        enable_multimodal_delays=_on("CEREBRO_MULTIMODAL"),
        enable_continuous_motor=_on("CEREBRO_CONTINUOUS_MOTOR"),
        enable_affordance_learning=_on("CEREBRO_AFFORDANCES"),
        enable_reward_learning=_on("CEREBRO_REWARD_LEARNING"),
        enable_rpe_surprise_coupling=_on("CEREBRO_RPE_SURPRISE"),
        enable_causal_transfer=_on("CEREBRO_CAUSAL_TRANSFER"),
        enable_latent_affordance=_on("CEREBRO_LATENT_LEARNING"),
        enable_schema_extinction=_on("CEREBRO_SCHEMA_EXTINCTION"),
        enable_model_based_deliberation=_on("CEREBRO_MODEL_BASED"),
        enable_metaplasticity_bcm=_on("CEREBRO_METAPLASTICITY"),
        enable_affect_dynamics=_on("CEREBRO_AFFECT_DYNAMICS"),
        enable_receptor_panel=_on("CEREBRO_RECEPTOR_PANEL"),
        enable_hpa_axis=_on("CEREBRO_HPA_AXIS"),
        enable_emotion_regulation=_on("CEREBRO_EMOTION_REG"),
        enable_empathy_contagion=_on("CEREBRO_EMPATHY"),
        enable_attachment_style=_on("CEREBRO_ATTACHMENT"),
        enable_social_shame=_on("CEREBRO_SOCIAL_SHAME"),
        enable_hedonic_wanting=_on("CEREBRO_WANTING"),
        enable_goal_frustration=_on("CEREBRO_FRUSTRATION"),
        enable_persistent_mood=_on("CEREBRO_PERSISTENT_MOOD"),
        enable_social_turns=_on("CEREBRO_SOCIAL_TURNS"),
        enable_language_dynamics=_on("CEREBRO_LANGUAGE_DYNAMICS"),
        enable_neural_language_default=_on("CEREBRO_NEURAL_LANG"),
        enable_curriculum_verbalization=_on("CEREBRO_CURRICULUM_VOICE"),
        enable_grounding_chat=_on("CEREBRO_GROUNDING"),
        enable_prosody=_on("CEREBRO_PROSODY"),
        enable_inner_outer_speech=_on("CEREBRO_INNER_SPEECH"),
        enable_broca_aphasia=_on("CEREBRO_BROCA_APHASIA", "0"),
        enable_wernicke_aphasia=_on("CEREBRO_WERNICKE_APHASIA", "0"),
        enable_bilingual_codeswitch=_on("CEREBRO_BILINGUAL"),
        enable_language_tutor_rag=_on("CEREBRO_LANGUAGE_TUTOR"),
        enable_motor_dynamics=_on("CEREBRO_MOTOR_DYNAMICS"),
        enable_cerebellum_adaptation=_on("CEREBRO_CEREBELLUM"),
        enable_basal_habituation=_on("CEREBRO_BASAL_HABIT"),
        enable_muscular_fatigue=_on("CEREBRO_MUSCULAR_FATIGUE"),
        enable_world_depth=_on("CEREBRO_WORLD_DEPTH"),
        enable_somatic_passive=_on("CEREBRO_SOMATIC"),
        enable_food_cycle=_on("CEREBRO_FOOD_CYCLE"),
        enable_desk_study_deterministic=_on("CEREBRO_DESK_STUDY"),
        enable_lifecycle_dynamics=_on("CEREBRO_LIFECYCLE_DYNAMICS"),
        enable_full_sleep_architecture=_on("CEREBRO_FULL_SLEEP"),
        enable_nocturnal_study=_on("CEREBRO_NOCTURNAL_STUDY"),
        enable_lifecycle_stages=_on("CEREBRO_LIFECYCLE_STAGES"),
        enable_puberty_hormones=_on("CEREBRO_PUBERTY"),
        enable_cognitive_aging=_on("CEREBRO_COGNITIVE_AGING"),
        enable_validation_dynamics=_on("CEREBRO_VALIDATION"),
        enable_observatory_hud=_on("CEREBRO_OBSERVATORY"),
        enable_neural_telemetry=_on("CEREBRO_TELEMETRY"),
        enable_sleep_study=_on("CEREBRO_SLEEP_STUDY"),
        enable_sleep_web=_on("CEREBRO_SLEEP_WEB"),
        # Demo: schemas desde hábitos + éxitos causales (Level 2.4).
        # Paper batch sigue con AblationFlags() → OFF.
    )
