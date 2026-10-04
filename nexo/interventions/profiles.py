"""Perfiles de lesión connectome — Sprint 11."""

from __future__ import annotations

from nexo.interventions.lesion import LesionSpec, LesionState

LESION_NONE = LesionSpec("lesion_none", "Conectoma intacto")

LESION_REGISTRY: dict[str, LesionSpec] = {
    "lesion_none": LESION_NONE,
    "lesion_sever_hippo_pfc": LesionSpec(
        "lesion_sever_hippo_pfc",
        "Corte hippocampus → prefrontal",
        sever=(("hippocampus", "prefrontal"),),
    ),
    "lesion_sever_pfc_bg": LesionSpec(
        "lesion_sever_pfc_bg",
        "Corte prefrontal → basal_ganglia",
        sever=(("prefrontal", "basal_ganglia"),),
    ),
    "lesion_sever_thal_visual": LesionSpec(
        "lesion_sever_thal_visual",
        "Corte thalamus_relay → visual_cortex",
        sever=(("thalamus_relay", "visual_cortex"),),
    ),
    "lesion_weaken_pfc_bg": LesionSpec(
        "lesion_weaken_pfc_bg",
        "Debilización prefrontal → basal_ganglia",
        weight_scale=(("prefrontal", "basal_ganglia", 0.25),),
    ),
    "lesion_delay_pfc_bg": LesionSpec(
        "lesion_delay_pfc_bg",
        "Latencia aumentada prefrontal → basal_ganglia",
        latency_add=(("prefrontal", "basal_ganglia", 5),),
    ),
}


def list_lesions() -> list[LesionSpec]:
    return list(LESION_REGISTRY.values())


def apply_lesion_profile(profile_id: str, state: LesionState | None = None) -> LesionState:
    spec = LESION_REGISTRY.get(profile_id, LESION_NONE)
    lesions = state or LesionState()
    spec.apply_to(lesions)
    return lesions
