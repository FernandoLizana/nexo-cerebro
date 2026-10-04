"""Registro de tareas conductuales integradas."""

from __future__ import annotations

from typing import Callable

from nexo.behavioral.results import IntegratedTaskResult
from nexo.behavioral.tasks import (
    run_autonomy_contract_audit_task,
    run_agent_loop_sync_smoke_task,
    run_agency_audit_smoke_task,
    run_causal_certificate_smoke_task,
    run_companion_dyad_smoke_task,
    run_day_in_the_life_smoke_task,
    run_curiosity_explore_task,
    run_deliberation_conflict_task,
    run_deliberation_weight_task,
    run_distractor_control_task,
    run_flask_demo_smoke_task,
    run_flask_study_proxy_smoke_task,
    run_flask_unified_e2e_task,
    run_foraging_task,
    run_hypothalamus_multimodal_smoke_task,
    run_legacy_adapter_timing_task,
    run_legacy_navigation_task,
    run_navigation_2d_task,
    run_memory_bridge_smoke_task,
    run_memory_unification_smoke_task,
    run_reproducibility_task,
    run_roadmap100_bridge_smoke_task,
    run_roadmap100_e_block_smoke_task,
    run_science_bundle_smoke_task,
    run_safety_escape_task,
    run_social_approach_task,
    run_survival_task,
    run_world2d_full_navigation_task,
    run_world2d_headless_navigation_task,
    run_unified_motor_smoke_task,
    run_world2d_legacy_env_navigation_task,
    run_world3d_state_sync_task,
    run_world_demo_facade_task,
)

TaskRunner = Callable[..., IntegratedTaskResult]

TASK_REGISTRY: dict[str, TaskRunner] = {
    "survival": run_survival_task,
    "distractor_control": run_distractor_control_task,
    "reproducibility": run_reproducibility_task,
    "safety_escape": run_safety_escape_task,
    "curiosity_explore": run_curiosity_explore_task,
    "social_approach": run_social_approach_task,
    "foraging": run_foraging_task,
    "navigation_2d": run_navigation_2d_task,
    "legacy_navigation": run_legacy_navigation_task,
    "world2d_full_navigation": run_world2d_full_navigation_task,
    "deliberation_conflict_resolution": run_deliberation_conflict_task,
    "deliberation_weight_sweep": run_deliberation_weight_task,
    "world2d_legacy_env_navigation": run_world2d_legacy_env_navigation_task,
    "legacy_adapter_timing": run_legacy_adapter_timing_task,
    "world2d_headless_navigation": run_world2d_headless_navigation_task,
    "roadmap100_bridge_smoke": run_roadmap100_bridge_smoke_task,
    "flask_demo_smoke": run_flask_demo_smoke_task,
    "flask_unified_e2e": run_flask_unified_e2e_task,
    "world3d_state_sync": run_world3d_state_sync_task,
    "autonomy_contract_audit": run_autonomy_contract_audit_task,
    "hypothalamus_multimodal_smoke": run_hypothalamus_multimodal_smoke_task,
    "companion_dyad_smoke": run_companion_dyad_smoke_task,
    "unified_motor_smoke": run_unified_motor_smoke_task,
    "world_demo_facade": run_world_demo_facade_task,
    "agent_loop_sync_smoke": run_agent_loop_sync_smoke_task,
    "memory_bridge_smoke": run_memory_bridge_smoke_task,
    "flask_study_proxy_smoke": run_flask_study_proxy_smoke_task,
    "roadmap100_e_block_smoke": run_roadmap100_e_block_smoke_task,
    "memory_unification_smoke": run_memory_unification_smoke_task,
    "causal_certificate_smoke": run_causal_certificate_smoke_task,
    "day_in_the_life_smoke": run_day_in_the_life_smoke_task,
    "agency_audit_smoke": run_agency_audit_smoke_task,
    "science_bundle_smoke": run_science_bundle_smoke_task,
}

DEFAULT_BATTERY_TASKS = ("survival", "distractor_control", "reproducibility")


def resolve_task_runners(task_ids: tuple[str, ...] | None = None) -> list[TaskRunner]:
    ids = task_ids or DEFAULT_BATTERY_TASKS
    return [TASK_REGISTRY[t] for t in ids if t in TASK_REGISTRY]
