"""Tareas conductuales sobre runtime integrado."""

from __future__ import annotations

from dataclasses import replace

from nexo.ablation.profiles import AblationProfile, INTEGRATED_FULL
from nexo.behavioral.metrics import compute_metrics
from nexo.behavioral.results import IntegratedTaskResult
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig


def base_integrated_config(
    *,
    seed: int = 42,
    ticks: int = 60,
    profile: str = "battery",
    intervention_mode: str = "integrated",
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    analysis_mode: str = "legacy",
    routing_mode: str = "legacy",
    world_mode: str = "room",
) -> IntegratedRuntimeConfig:
    return IntegratedRuntimeConfig(
        seed=seed,
        ticks=ticks,
        profile=profile,
        perception_mode="predictive",
        memory_mode="integrated",
        executive_mode="integrated",
        learning_mode="integrated",
        consciousness_mode="integrated",
        social_mode="integrated",
        sleep_mode="integrated",
        evaluation_mode="integrated",
        intervention_mode=intervention_mode,
        lesion_profile=lesion_profile,
        latency_mode=latency_mode,
        analysis_mode=analysis_mode,
        routing_mode=routing_mode,
        world_mode=world_mode,
    )


def run_survival_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 60,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    cfg = ablation.apply(
        base_integrated_config(
            seed=seed,
            ticks=ticks,
            lesion_profile=lesion_profile,
            latency_mode=latency_mode,
            routing_mode=routing_mode,
        )
    )
    rt = IntegratedRuntime(cfg)
    result = rt.run()
    metrics = compute_metrics(rt, result)
    return IntegratedTaskResult(
        task_id="survival",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "survival_success": metrics["survival_success"],
            "final_energy": metrics["final_energy"],
            "mean_reward": metrics["mean_reward"],
        },
        secondary_metrics=metrics,
        details={
            "trajectory_hash": result["trajectory_hash"],
            "profile": cfg.profile,
            "lesion_id": lesion_profile,
            "latency_mode": latency_mode,
            "routing_mode": routing_mode,
        },
    )


def run_distractor_control_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 50,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    cfg = ablation.apply(
        base_integrated_config(
            seed=seed,
            ticks=ticks,
            lesion_profile=lesion_profile,
            latency_mode=latency_mode,
            routing_mode=routing_mode,
        )
    )
    rt = IntegratedRuntime(replace(cfg, profile=f"{cfg.profile}_distractor"))
    rt.world.distractor_salience = 0.75
    rt.world.energy = 0.35
    rt.body.energy = 0.35
    result = rt.run()
    metrics = compute_metrics(rt, result)
    adaptive = metrics["eat_ratio"] / max(metrics["distractor_ratio"], 0.01)
    return IntegratedTaskResult(
        task_id="distractor_control",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "eat_ratio": metrics["eat_ratio"],
            "distractor_ratio": metrics["distractor_ratio"],
            "adaptation_score": min(1.0, adaptive / 3.0),
        },
        secondary_metrics=metrics,
        details={
            "trajectory_hash": result["trajectory_hash"],
            "lesion_id": lesion_profile,
            "latency_mode": latency_mode,
            "routing_mode": routing_mode,
        },
    )


def run_reproducibility_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 40,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    cfg = ablation.apply(
        base_integrated_config(
            seed=seed,
            ticks=ticks,
            lesion_profile=lesion_profile,
            latency_mode=latency_mode,
            routing_mode=routing_mode,
        )
    )
    r1 = IntegratedRuntime(cfg).run()
    r2 = IntegratedRuntime(cfg).run()
    match = r1["trajectory_hash"] == r2["trajectory_hash"]
    return IntegratedTaskResult(
        task_id="reproducibility",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={"trajectory_match": 1.0 if match else 0.0},
        details={
            "hash_a": r1["trajectory_hash"],
            "hash_b": r2["trajectory_hash"],
            "lesion_id": lesion_profile,
            "latency_mode": latency_mode,
            "routing_mode": routing_mode,
        },
    )


def run_safety_escape_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 55,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    """Escape ante peligro elevado — mide respuesta de huida."""
    cfg = ablation.apply(
        base_integrated_config(
            seed=seed,
            ticks=ticks,
            lesion_profile=lesion_profile,
            latency_mode=latency_mode,
            routing_mode=routing_mode,
        )
    )
    rt = IntegratedRuntime(replace(cfg, profile=f"{cfg.profile}_safety"))
    rt.world.danger_level = 0.85
    rt.world.energy = 0.45
    rt.body.energy = 0.45
    result = rt.run()
    metrics = compute_metrics(rt, result)
    flee_ratio = metrics["flee_ratio"]
    return IntegratedTaskResult(
        task_id="safety_escape",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "flee_ratio": flee_ratio,
            "survival_success": metrics["survival_success"],
            "safety_response": min(1.0, flee_ratio * 2.0),
        },
        secondary_metrics=metrics,
        details={
            "trajectory_hash": result["trajectory_hash"],
            "lesion_id": lesion_profile,
            "latency_mode": latency_mode,
            "routing_mode": routing_mode,
            "danger_level": 0.85,
        },
    )


def run_curiosity_explore_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 50,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    """Exploración bajo bajo peligro y distractor saliente — mide curiosidad."""
    cfg = ablation.apply(
        base_integrated_config(
            seed=seed,
            ticks=ticks,
            lesion_profile=lesion_profile,
            latency_mode=latency_mode,
            routing_mode=routing_mode,
        )
    )
    rt = IntegratedRuntime(replace(cfg, profile=f"{cfg.profile}_curiosity"))
    rt.world.danger_level = 0.05
    rt.world.distractor_salience = 0.9
    rt.world.energy = 0.55
    rt.body.energy = 0.55
    result = rt.run()
    metrics = compute_metrics(rt, result)
    explore_ratio = metrics["explore_ratio"]
    entropy_norm = min(1.0, metrics["action_entropy"] / 2.0)
    return IntegratedTaskResult(
        task_id="curiosity_explore",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "explore_ratio": explore_ratio,
            "action_entropy": metrics["action_entropy"],
            "curiosity_score": min(1.0, explore_ratio * 1.2 + entropy_norm * 0.4),
        },
        secondary_metrics=metrics,
        details={
            "trajectory_hash": result["trajectory_hash"],
            "lesion_id": lesion_profile,
            "latency_mode": latency_mode,
            "routing_mode": routing_mode,
            "danger_level": 0.05,
            "distractor_salience": 0.9,
        },
    )


def run_social_approach_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 50,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    """Acercamiento social al cuidador bajo necesidad social elevada."""
    cfg = ablation.apply(
        base_integrated_config(
            seed=seed,
            ticks=ticks,
            lesion_profile=lesion_profile,
            latency_mode=latency_mode,
            routing_mode=routing_mode,
        )
    )
    rt = IntegratedRuntime(replace(cfg, profile=f"{cfg.profile}_social"))
    rt.world.caregiver_present = True
    rt.world.caregiver_trust = 0.35
    rt.world.danger_level = 0.08
    rt.world.energy = 0.4
    rt.body.energy = 0.4
    trust_before = rt.world.caregiver_trust
    result = rt.run()
    trust_after = rt.world.caregiver_trust
    metrics = compute_metrics(rt, result)
    actions = result.get("actions_taken") or []
    total = max(len(actions), 1)
    approach_ratio = sum(1 for a in actions if a == "approach_caregiver") / total
    return IntegratedTaskResult(
        task_id="social_approach",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "approach_ratio": approach_ratio,
            "caregiver_trust_delta": trust_after - trust_before,
            "social_score": min(1.0, approach_ratio * 2.0 + max(0.0, trust_after - trust_before)),
        },
        secondary_metrics=metrics,
        details={
            "trajectory_hash": result["trajectory_hash"],
            "lesion_id": lesion_profile,
            "latency_mode": latency_mode,
            "routing_mode": routing_mode,
            "caregiver_trust_initial": trust_before,
            "caregiver_trust_final": trust_after,
        },
    )


def run_foraging_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 55,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    """Forrajeo bajo clima adverso en ExtendedRoomWorld."""
    cfg = ablation.apply(
        base_integrated_config(
            seed=seed,
            ticks=ticks,
            lesion_profile=lesion_profile,
            latency_mode=latency_mode,
            routing_mode=routing_mode,
            world_mode="extended",
        )
    )
    rt = IntegratedRuntime(replace(cfg, profile=f"{cfg.profile}_foraging"))
    rt.world.weather_level = 0.72
    rt.world.food_available = False
    rt.world.energy = 0.38
    rt.body.energy = 0.38
    result = rt.run()
    metrics = compute_metrics(rt, result)
    shelter_ratio = metrics.get("shelter_ratio", 0.0)
    return IntegratedTaskResult(
        task_id="foraging",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "shelter_ratio": shelter_ratio,
            "survival_success": metrics["survival_success"],
            "foraging_score": min(1.0, shelter_ratio * 1.5 + metrics["survival_success"] * 0.5),
        },
        secondary_metrics=metrics,
        details={
            "trajectory_hash": result["trajectory_hash"],
            "lesion_id": lesion_profile,
            "world_mode": "extended",
            "weather_level": 0.72,
        },
    )


def run_navigation_2d_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 50,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    """Navegación en World2D lite — mide desplazamiento espacial."""
    cfg = ablation.apply(
        base_integrated_config(
            seed=seed,
            ticks=ticks,
            lesion_profile=lesion_profile,
            latency_mode=latency_mode,
            routing_mode=routing_mode,
            world_mode="world2d_lite",
        )
    )
    rt = IntegratedRuntime(replace(cfg, profile=f"{cfg.profile}_nav2d"))
    rt.world.food_available = True
    result = rt.run()
    metrics = compute_metrics(rt, result)
    explore_ratio = metrics["explore_ratio"]
    distance = metrics.get("distance_traveled", 0.0)
    return IntegratedTaskResult(
        task_id="navigation_2d",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "explore_ratio": explore_ratio,
            "distance_traveled": distance,
            "navigation_score": min(1.0, explore_ratio + distance / 200.0),
        },
        secondary_metrics=metrics,
        details={
            "trajectory_hash": result["trajectory_hash"],
            "world_mode": "world2d_lite",
            "lesion_id": lesion_profile,
        },
    )


def run_legacy_navigation_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 45,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    """Navegación con mapeo choice_key legacy en World2D lite."""
    from nexo.demo.world2d_actions import LEGACY_TO_INTEGRATED, map_legacy_action

    cfg = ablation.apply(
        base_integrated_config(
            seed=seed,
            ticks=ticks,
            lesion_profile=lesion_profile,
            latency_mode=latency_mode,
            routing_mode=routing_mode,
            world_mode="world2d_lite",
        )
    )
    rt = IntegratedRuntime(
        replace(cfg, profile=f"{cfg.profile}_legnav", world2d_legacy_actions_mode="integrated")
    )
    result = rt.run()
    metrics = compute_metrics(rt, result)
    sample_keys = ("tv", "research", "eat", "wander")
    coverage = sum(1 for k in sample_keys if k in LEGACY_TO_INTEGRATED) / len(sample_keys)
    mapped_actions = {k: map_legacy_action(k) for k in sample_keys}
    return IntegratedTaskResult(
        task_id="legacy_navigation",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "mapping_coverage": coverage,
            "distance_traveled": metrics.get("distance_traveled", 0.0),
            "legacy_nav_score": min(1.0, coverage * 0.6 + metrics.get("explore_ratio", 0.0)),
        },
        secondary_metrics=metrics,
        details={
            "trajectory_hash": result["trajectory_hash"],
            "world_mode": "world2d_lite",
            "mapped_actions": mapped_actions,
        },
    )


def run_world2d_full_navigation_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 45,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    """Navegación World2D con catálogo completo choice_key legacy."""
    from nexo.demo.world2d_actions import FULL_LEGACY_CATALOG, full_catalog_coverage, map_legacy_action

    cfg = ablation.apply(
        base_integrated_config(
            seed=seed,
            ticks=ticks,
            lesion_profile=lesion_profile,
            latency_mode=latency_mode,
            routing_mode=routing_mode,
            world_mode="world2d_lite",
        )
    )
    rt = IntegratedRuntime(
        replace(
            cfg,
            profile=f"{cfg.profile}_w2dfull",
            world2d_legacy_actions_mode="integrated",
            world2d_full_actions_mode="integrated",
        )
    )
    result = rt.run()
    metrics = compute_metrics(rt, result)
    sample_keys = tuple(FULL_LEGACY_CATALOG.keys())[:8]
    coverage = full_catalog_coverage()
    mapped_actions = {k: map_legacy_action(k, full=True) for k in sample_keys}
    return IntegratedTaskResult(
        task_id="world2d_full_navigation",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "full_catalog_coverage": coverage,
            "distance_traveled": metrics.get("distance_traveled", 0.0),
            "full_nav_score": min(1.0, coverage * 0.7 + metrics.get("explore_ratio", 0.0)),
        },
        secondary_metrics=metrics,
        details={
            "trajectory_hash": result["trajectory_hash"],
            "world_mode": "world2d_lite",
            "mapped_actions": mapped_actions,
            "catalog_size": len(FULL_LEGACY_CATALOG),
        },
    )


def run_deliberation_conflict_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 40,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    """Escenario con legacy adapter + fusión unificada motora."""
    from nexo.behavioral.deliberation_unified import summarize_deliberation_unified

    cfg = ablation.apply(
        base_integrated_config(
            seed=seed,
            ticks=ticks,
            lesion_profile=lesion_profile,
            latency_mode=latency_mode,
            routing_mode=routing_mode,
        )
    )
    rt = IntegratedRuntime(
        replace(
            cfg,
            profile=f"{cfg.profile}_delibconf",
            deliberation_bridge_mode="integrated",
            deliberation_fusion_mode="integrated",
            deliberation_unified_mode="integrated",
            legacy_adapter_mode="integrated",
        )
    )
    result = rt.run()
    metrics = compute_metrics(rt, result)
    summary = summarize_deliberation_unified(rt)
    return IntegratedTaskResult(
        task_id="deliberation_conflict_resolution",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "unified_events": float(summary["unified_events"]),
            "agreement_rate": summary["agreement_rate"],
            "conflict_score": min(1.0, summary["unified_events"] / max(ticks, 1)),
        },
        secondary_metrics=metrics,
        details={
            "trajectory_hash": result["trajectory_hash"],
            "deliberation_summary": summary,
        },
    )


def run_world2d_legacy_env_navigation_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 50,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    """Navegación en entorno legacy enriquecido (mobiliario + habitaciones)."""
    cfg = ablation.apply(
        base_integrated_config(
            seed=seed,
            ticks=ticks,
            lesion_profile=lesion_profile,
            latency_mode=latency_mode,
            routing_mode=routing_mode,
            world_mode="world2d_legacy_env",
        )
    )
    rt = IntegratedRuntime(
        replace(
            cfg,
            profile=f"{cfg.profile}_w2denv",
            world2d_legacy_env_mode="integrated",
            world2d_legacy_actions_mode="integrated",
            world2d_full_actions_mode="integrated",
        )
    )
    result = rt.run()
    metrics = compute_metrics(rt, result)
    world = rt.world
    fidelity = getattr(world, "env_fidelity_score", lambda: 0.0)()
    return IntegratedTaskResult(
        task_id="world2d_legacy_env_navigation",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "env_fidelity": fidelity,
            "distance_traveled": metrics.get("distance_traveled", 0.0),
            "legacy_env_score": min(1.0, fidelity * 0.6 + metrics.get("explore_ratio", 0.0)),
        },
        secondary_metrics=metrics,
        details={
            "trajectory_hash": result["trajectory_hash"],
            "world_mode": "world2d_legacy_env",
            "furniture_count": getattr(world, "furniture_count", 0),
            "rooms_visited": len(getattr(world, "rooms_visited", set())),
        },
    )


def run_deliberation_weight_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 40,
    legacy_weight: float = 0.6,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    """Conflicto deliberación con peso legacy configurable."""
    from nexo.behavioral.deliberation_weight import summarize_deliberation_weight

    cfg = ablation.apply(
        base_integrated_config(
            seed=seed,
            ticks=ticks,
            lesion_profile=lesion_profile,
            latency_mode=latency_mode,
            routing_mode=routing_mode,
        )
    )
    rt = IntegratedRuntime(
        replace(
            cfg,
            profile=f"{cfg.profile}_delibw",
            deliberation_bridge_mode="integrated",
            deliberation_fusion_mode="integrated",
            deliberation_weight_mode="integrated",
            deliberation_unified_mode="legacy",
            legacy_advisory_weight=legacy_weight,
            legacy_adapter_mode="integrated",
        )
    )
    result = rt.run()
    metrics = compute_metrics(rt, result)
    summary = summarize_deliberation_weight(rt)
    return IntegratedTaskResult(
        task_id="deliberation_weight_sweep",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "legacy_weight": legacy_weight,
            "legacy_picks": float(summary["legacy_picks"]),
            "integrated_picks": float(summary["integrated_picks"]),
            "weight_score": summary["legacy_picks"] / max(summary["weighted_events"], 1),
        },
        secondary_metrics=metrics,
        details={
            "trajectory_hash": result["trajectory_hash"],
            "weight_summary": summary,
        },
    )


def run_legacy_adapter_timing_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 40,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    """Verifica legacy adapter temprano (priority 61) vs integrado."""
    from nexo.behavioral.legacy_adapter_early import summarize_legacy_adapter_early

    cfg = ablation.apply(
        base_integrated_config(
            seed=seed,
            ticks=ticks,
            lesion_profile=lesion_profile,
            latency_mode=latency_mode,
            routing_mode=routing_mode,
        )
    )
    rt = IntegratedRuntime(
        replace(
            cfg,
            profile=f"{cfg.profile}_legearly",
            legacy_adapter_mode="integrated",
            legacy_adapter_early_mode="integrated",
        )
    )
    result = rt.run()
    metrics = compute_metrics(rt, result)
    summary = summarize_legacy_adapter_early(rt)
    return IntegratedTaskResult(
        task_id="legacy_adapter_timing",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "same_tick_pairs": float(summary["same_tick_pairs"]),
            "legacy_action_events": float(summary["legacy_action_events"]),
            "timing_score": min(1.0, summary["same_tick_pairs"] / max(ticks, 1)),
        },
        secondary_metrics=metrics,
        details={"trajectory_hash": result["trajectory_hash"], "timing_summary": summary},
    )


def run_world2d_headless_navigation_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 50,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    """Navegación World2D headless con step_toward."""
    cfg = ablation.apply(
        base_integrated_config(
            seed=seed,
            ticks=ticks,
            lesion_profile=lesion_profile,
            latency_mode=latency_mode,
            routing_mode=routing_mode,
            world_mode="world2d_headless",
        )
    )
    rt = IntegratedRuntime(
        replace(
            cfg,
            profile=f"{cfg.profile}_w2dh",
            world2d_headless_mode="integrated",
            world2d_legacy_env_mode="integrated",
        )
    )
    result = rt.run()
    metrics = compute_metrics(rt, result)
    world = rt.world
    fidelity = getattr(world, "headless_fidelity_score", lambda: 0.0)()
    return IntegratedTaskResult(
        task_id="world2d_headless_navigation",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "headless_fidelity": fidelity,
            "headless_steps": float(getattr(world, "headless_steps", 0)),
            "headless_nav_score": min(1.0, fidelity + metrics.get("explore_ratio", 0.0) * 0.3),
        },
        secondary_metrics=metrics,
        details={
            "trajectory_hash": result["trajectory_hash"],
            "world_mode": "world2d_headless",
            "furniture_proximity_events": getattr(world, "furniture_proximity_events", 0),
        },
    )


def run_roadmap100_bridge_smoke_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 35,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    """Smoke puente roadmap100 flags en legacy brain."""
    from nexo.behavioral.roadmap100_bridge import summarize_roadmap100_bridge

    cfg = ablation.apply(
        base_integrated_config(
            seed=seed,
            ticks=ticks,
            lesion_profile=lesion_profile,
            latency_mode=latency_mode,
            routing_mode=routing_mode,
        )
    )
    rt = IntegratedRuntime(
        replace(
            cfg,
            profile=f"{cfg.profile}_r100",
            legacy_adapter_mode="integrated",
            roadmap100_bridge_mode="integrated",
        )
    )
    result = rt.run()
    metrics = compute_metrics(rt, result)
    summary = summarize_roadmap100_bridge(rt)
    coverage = summary.get("roadmap100_flags", {}).get("coverage", 0.0)
    return IntegratedTaskResult(
        task_id="roadmap100_bridge_smoke",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "roadmap100_coverage": coverage,
            "bridge_events": float(summary["bridge_events"]),
            "bridge_score": min(1.0, coverage * 0.7 + summary["bridge_events"] / max(ticks, 1) * 0.3),
        },
        secondary_metrics=metrics,
        details={"trajectory_hash": result["trajectory_hash"], "bridge_summary": summary},
    )


def _fase10_runtime_config(cfg: IntegratedRuntimeConfig, suffix: str, **modes: str) -> IntegratedRuntimeConfig:
    base = replace(
        cfg,
        profile=f"{cfg.profile}_{suffix}",
        legacy_adapter_mode="integrated",
        legacy_adapter_early_mode="integrated",
        roadmap100_bridge_mode="integrated",
    )
    return replace(base, **modes)


def run_flask_demo_smoke_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 30,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    from nexo.behavioral.flask_demo_bridge import summarize_flask_demo_bridge

    cfg = ablation.apply(
        base_integrated_config(seed=seed, ticks=ticks, lesion_profile=lesion_profile,
                               latency_mode=latency_mode, routing_mode=routing_mode)
    )
    rt = IntegratedRuntime(_fase10_runtime_config(cfg, "flask", flask_demo_bridge_mode="integrated"))
    result = rt.run()
    metrics = compute_metrics(rt, result)
    summary = summarize_flask_demo_bridge(rt)
    return IntegratedTaskResult(
        task_id="flask_demo_smoke",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "bridge_score": summary["bridge_score"],
            "bridge_events": float(summary["bridge_events"]),
            "hud_ready": float(summary["hud_ready"]),
        },
        secondary_metrics=metrics,
        details={"trajectory_hash": result["trajectory_hash"], "bridge_summary": summary},
    )


def run_world3d_state_sync_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 45,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    from nexo.behavioral.world3d_sync_report import summarize_world3d_sync

    cfg = ablation.apply(
        base_integrated_config(
            seed=seed, ticks=ticks, lesion_profile=lesion_profile,
            latency_mode=latency_mode, routing_mode=routing_mode,
            world_mode="world3d_sync",
        )
    )
    rt = IntegratedRuntime(
        _fase10_runtime_config(
            cfg, "w3d",
            world3d_sync_mode="integrated",
            world2d_headless_mode="integrated",
        )
    )
    result = rt.run()
    metrics = compute_metrics(rt, result)
    summary = summarize_world3d_sync(rt)
    return IntegratedTaskResult(
        task_id="world3d_state_sync",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "sync_score": summary["sync_score"],
            "fidelity": summary["fidelity"],
            "furniture_count": float(summary["furniture_count"]),
        },
        secondary_metrics=metrics,
        details={"trajectory_hash": result["trajectory_hash"], "sync_summary": summary},
    )


def run_autonomy_contract_audit_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 35,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    from nexo.behavioral.autonomy_guard import summarize_autonomy_guard

    cfg = ablation.apply(
        base_integrated_config(seed=seed, ticks=ticks, lesion_profile=lesion_profile,
                               latency_mode=latency_mode, routing_mode=routing_mode)
    )
    rt = IntegratedRuntime(_fase10_runtime_config(cfg, "auto", autonomy_guard_mode="integrated"))
    result = rt.run()
    metrics = compute_metrics(rt, result)
    summary = summarize_autonomy_guard(rt)
    return IntegratedTaskResult(
        task_id="autonomy_contract_audit",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "guard_score": summary["guard_score"],
            "app_audit_score": summary["app_route_audit"]["audit_score"],
            "deliberation_selects_actions": float(summary["deliberation_selects_actions"]),
        },
        secondary_metrics=metrics,
        details={"trajectory_hash": result["trajectory_hash"], "guard_summary": summary},
    )


def run_hypothalamus_multimodal_smoke_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 40,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    from nexo.behavioral.hypothalamus_multimodal import summarize_hypothalamus_multimodal

    cfg = ablation.apply(
        base_integrated_config(seed=seed, ticks=ticks, lesion_profile=lesion_profile,
                               latency_mode=latency_mode, routing_mode=routing_mode)
    )
    rt = IntegratedRuntime(
        _fase10_runtime_config(cfg, "hypo", hypothalamus_multimodal_mode="integrated")
    )
    result = rt.run()
    metrics = compute_metrics(rt, result)
    summary = summarize_hypothalamus_multimodal(rt)
    return IntegratedTaskResult(
        task_id="hypothalamus_multimodal_smoke",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "multimodal_score": summary["multimodal_score"],
            "multimodal_events": float(summary["multimodal_events"]),
            "legacy_hypothalamus_present": float(summary["legacy_hypothalamus_present"]),
        },
        secondary_metrics=metrics,
        details={"trajectory_hash": result["trajectory_hash"], "hypo_summary": summary},
    )


def run_companion_dyad_smoke_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 50,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    from nexo.behavioral.companion_integrated import summarize_companion_integrated

    cfg = ablation.apply(
        base_integrated_config(
            seed=seed, ticks=ticks, lesion_profile=lesion_profile,
            latency_mode=latency_mode, routing_mode=routing_mode,
            world_mode="world3d_sync",
        )
    )
    rt = IntegratedRuntime(
        _fase10_runtime_config(
            cfg, "nira",
            companion_integrated_mode="integrated",
            world3d_sync_mode="integrated",
        )
    )
    result = rt.run()
    metrics = compute_metrics(rt, result)
    summary = summarize_companion_integrated(rt)
    return IntegratedTaskResult(
        task_id="companion_dyad_smoke",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "dyad_score": summary["dyad_score"],
            "dyad_events": float(summary["dyad_events"]),
            "bond": summary["bond"],
        },
        secondary_metrics=metrics,
        details={"trajectory_hash": result["trajectory_hash"], "companion_summary": summary},
    )


def run_flask_unified_e2e_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 30,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    """E2E sesión Flask unificada — legacy tick + sidecar integrado."""
    from dataclasses import replace as dc_replace

    from brain.experiment_flags import AblationFlags
    from brain.mind import InfantApeBrain
    from brain.profile import COMPACT_PROFILE
    from nexo.demo.flask_unified import create_unified_session
    from nexo.integrated_runtime import _repo_root

    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        headless=True,
        auto_save=False,
        seed=seed,
        experiment_flags=dc_replace(AblationFlags(), enable_neural_telemetry=True),
    )
    brain.world.ensure_home()
    brain.ensure_companion()
    session = create_unified_session(
        brain,
        _repo_root() / "configs/nexo/flask_unified_v2.yaml",
    )
    out = session.world_tick(steps=ticks)
    status = session.status()
    integrated = out.get("integrated") or {}
    return IntegratedTaskResult(
        task_id="flask_unified_e2e",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "unified": 1.0,
            "game3d_fidelity": float(integrated.get("game3d_fidelity", 0.0)),
            "bridge_score": float(status["bridge_summary"]["bridge_score"]),
            "integrated_ticks": float(status["integrated_clock"]),
        },
        secondary_metrics={},
        details={
            "integrated_profile": session.runtime.config.profile,
            "flask_unified_mode": session.runtime.config.flask_unified_mode,
            "trajectory_hash": integrated.get("trajectory_hash"),
        },
    )


def run_world_demo_facade_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 40,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    from brain.mind import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    cfg = ablation.apply(
        base_integrated_config(
            seed=seed,
            ticks=ticks,
            lesion_profile=lesion_profile,
            latency_mode=latency_mode,
            routing_mode=routing_mode,
            world_mode="world_demo_facade",
        )
    )
    brain = InfantApeBrain(profile=COMPACT_PROFILE, headless=True, auto_save=False, seed=seed)
    brain.world.ensure_home()
    rt = IntegratedRuntime(
        replace(
            cfg,
            profile=f"{cfg.profile}_wdf",
            legacy_adapter_mode="integrated",
            world_mode="world_demo_facade",
            world2d_legacy_env_mode="integrated",
            world2d_legacy_actions_mode="integrated",
        ),
        legacy_brain=brain,
    )
    result = rt.run()
    metrics = compute_metrics(rt, result)
    fidelity = getattr(rt.world, "facade_fidelity_score", lambda: 0.0)()
    return IntegratedTaskResult(
        task_id="world_demo_facade",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "facade_fidelity": fidelity,
            "furniture_count": float(getattr(rt.world, "furniture_count", 0)),
            "shared_world": float(getattr(rt.world, "_env", None) is not None and rt.world._env._world2d is brain.world),
        },
        secondary_metrics=metrics,
        details={"trajectory_hash": result["trajectory_hash"]},
    )


def run_unified_motor_smoke_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 35,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    from nexo.behavioral.unified_motor import summarize_unified_motor
    from nexo.demo.flask_unified import create_unified_session
    from brain.mind import InfantApeBrain
    from brain.profile import COMPACT_PROFILE
    from nexo.integrated_runtime import _repo_root

    brain = InfantApeBrain(profile=COMPACT_PROFILE, headless=True, auto_save=False, seed=seed)
    brain.world.ensure_home()
    session = create_unified_session(brain, _repo_root() / "configs/nexo/flask_unified_v2.yaml")
    session.world_tick(steps=ticks)
    summary = summarize_unified_motor(session.runtime)
    return IntegratedTaskResult(
        task_id="unified_motor_smoke",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "motor_score": summary["motor_score"],
            "motor_events": float(summary["motor_events"]),
            "motor_authority_integrated": float(summary["motor_authority"] == "integrated"),
        },
        secondary_metrics={},
        details={
            "motor_summary": summary,
            "integrated_profile": session.runtime.config.profile,
        },
    )


def run_agent_loop_sync_smoke_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 30,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    from nexo.behavioral.agent_loop_sync import summarize_agent_loop_sync
    from nexo.demo.flask_unified import create_unified_session
    from brain.mind import InfantApeBrain
    from brain.profile import COMPACT_PROFILE
    from nexo.integrated_runtime import _repo_root

    brain = InfantApeBrain(profile=COMPACT_PROFILE, headless=True, auto_save=False, seed=seed)
    brain.world.ensure_home()
    brain.ensure_companion()
    session = create_unified_session(brain, _repo_root() / "configs/nexo/flask_unified_v3.yaml")
    out = session.world_tick(steps=ticks)
    summary = summarize_agent_loop_sync(session.runtime)
    lite = (out.get("integrated") or {}).get("agent_loop_sync") or {}
    return IntegratedTaskResult(
        task_id="agent_loop_sync_smoke",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "sync_score": summary["sync_score"],
            "lite_sync_runs": float(summary["lite_sync_runs"]),
            "thought_len": float(lite.get("thought_len", 0)),
        },
        secondary_metrics={},
        details={"sync_summary": summary, "lite_sync": lite},
    )


def run_memory_bridge_smoke_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 35,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    from nexo.behavioral.memory_bridge import summarize_memory_bridge
    from nexo.integrated_runtime import runtime_from_config, _repo_root

    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v70.yaml")
    rt.config.seed = seed
    rt.config.ticks = ticks
    rt.run()
    summary = summarize_memory_bridge(rt)
    return IntegratedTaskResult(
        task_id="memory_bridge_smoke",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "bridge_score": summary["bridge_score"],
            "bridge_events": float(summary["bridge_events"]),
            "live_parity_ratio": summary["live_parity_ratio"],
        },
        secondary_metrics={},
        details={"bridge_summary": summary},
    )


def run_flask_study_proxy_smoke_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 10,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    from brain.curriculum import get_section, study_section
    from nexo.demo.flask_study_proxy import wrap_study_response
    from nexo.demo.flask_unified import create_unified_session
    from brain.mind import InfantApeBrain
    from brain.profile import COMPACT_PROFILE
    from nexo.integrated_runtime import _repo_root

    brain = InfantApeBrain(profile=COMPACT_PROFILE, headless=True, auto_save=False, seed=seed)
    brain.world.ensure_home()
    session = create_unified_session(brain, _repo_root() / "configs/nexo/flask_unified_v3.yaml")
    section = get_section(None) or brain.curriculum.suggest_next()
    assert section is not None
    result = study_section(brain, section)
    payload = wrap_study_response(
        session,
        {
            "studied": section.to_dict(done=True),
            "curriculum": brain.curriculum.to_dict(),
            "learning": result.get("learning"),
        },
        track="curriculum",
    )
    block = payload.get("integrated_study") or {}
    return IntegratedTaskResult(
        task_id="flask_study_proxy_smoke",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "study_proxy": float(block.get("unified", False)),
            "integrated_ticks": float(block.get("integrated_ticks", 0)),
            "memory_bridge_score": float((block.get("memory_bridge") or {}).get("bridge_score", 0.0)),
        },
        secondary_metrics={},
        details={"integrated_study": block},
    )


def run_roadmap100_e_block_smoke_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 40,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    from nexo.behavioral.roadmap100_e_block import audit_e_block_conditions, summarize_roadmap100_e_block
    from nexo.integrated_runtime import runtime_from_config, _repo_root

    audit = audit_e_block_conditions()
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v70.yaml")
    rt.config.seed = seed
    rt.config.ticks = ticks
    rt.run()
    summary = summarize_roadmap100_e_block(rt)
    return IntegratedTaskResult(
        task_id="roadmap100_e_block_smoke",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "e_block_score": summary["e_block_score"],
            "condition_coverage": summary["condition_coverage"],
            "catalog_resolved": float(audit["resolved_count"]),
        },
        secondary_metrics={},
        details={"audit": audit, "summary": summary},
    )


def run_memory_unification_smoke_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 80,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    import tempfile
    from pathlib import Path

    from brain.mind import InfantApeBrain
    from brain.profile import COMPACT_PROFILE
    from nexo.behavioral.memory_unification import summarize_memory_unification
    from nexo.integrated_runtime import runtime_from_config, _repo_root

    sd = Path(tempfile.mkdtemp(prefix="nexo_unif_"))
    brain = InfantApeBrain(profile=COMPACT_PROFILE, state_dir=sd, headless=True, auto_save=False, seed=seed)
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v80.yaml", legacy_brain=brain)
    rt.config.seed = seed
    rt.config.ticks = ticks
    rt.run()
    summary = summarize_memory_unification(rt)
    return IntegratedTaskResult(
        task_id="memory_unification_smoke",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "unification_score": summary["unification_score"],
            "promoted_count": float(summary["promoted_count"]),
        },
        secondary_metrics={},
        details={"summary": summary},
    )


def run_causal_certificate_smoke_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 40,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    from nexo.behavioral.causal_certificate import summarize_causal_certificates
    from nexo.integrated_runtime import runtime_from_config, _repo_root

    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v90.yaml")
    rt.config.seed = seed
    rt.config.ticks = ticks
    rt.run()
    summary = summarize_causal_certificates(rt)
    return IntegratedTaskResult(
        task_id="causal_certificate_smoke",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "certificate_score": summary["certificate_score"],
            "valid_certificates": float(summary["valid_certificates"]),
        },
        secondary_metrics={},
        details={"summary": summary},
    )


def run_day_in_the_life_smoke_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int | None = None,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    import tempfile
    from pathlib import Path

    from brain.mind import InfantApeBrain
    from brain.profile import COMPACT_PROFILE
    from nexo.demo.day_in_the_life import build_day_timeline, day_in_the_life_ticks
    from nexo.integrated_runtime import runtime_from_config, _repo_root

    sd = Path(tempfile.mkdtemp(prefix="nexo_day_"))
    brain = InfantApeBrain(profile=COMPACT_PROFILE, state_dir=sd, headless=True, auto_save=False, seed=seed)
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v80.yaml", legacy_brain=brain)
    rt.config.seed = seed
    n = ticks or day_in_the_life_ticks(simulated_hours=24.0, seconds_per_tick=rt.clock.seconds_per_tick)
    rt.config.ticks = n
    rt.run()
    timeline = build_day_timeline(rt)
    return IntegratedTaskResult(
        task_id="day_in_the_life_smoke",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "simulated_hours": timeline["simulated_hours"],
            "sleep_phase_changes": float(timeline["sleep_phase_changes"]),
            "causal_certificates": float(timeline["causal_certificates"]),
        },
        secondary_metrics={},
        details={"timeline": timeline},
    )


def run_agency_audit_smoke_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 40,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    from nexo.behavioral.agency_audit import summarize_agency_audit
    from nexo.integrated_runtime import runtime_from_config, _repo_root

    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v90.yaml")
    rt.config.seed = seed
    rt.config.ticks = ticks
    rt.run()
    summary = summarize_agency_audit(rt)
    return IntegratedTaskResult(
        task_id="agency_audit_smoke",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "agency_score": summary["agency_score"],
            "certificate_score": summary["certificate_score"],
            "agency_valid_certificates": float(summary["agency_valid_certificates"]),
        },
        secondary_metrics={},
        details={"summary": summary},
    )


def run_science_bundle_smoke_task(
    *,
    ablation: AblationProfile = INTEGRATED_FULL,
    seed: int = 42,
    ticks: int = 30,
    lesion_profile: str = "lesion_none",
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> IntegratedTaskResult:
    import tempfile
    from pathlib import Path

    from brain.mind import InfantApeBrain
    from brain.profile import COMPACT_PROFILE
    from nexo.behavioral.science_bundle import export_science_bundle
    from nexo.integrated_runtime import runtime_from_config, _repo_root

    sd = Path(tempfile.mkdtemp(prefix="nexo_science_"))
    brain = InfantApeBrain(profile=COMPACT_PROFILE, state_dir=sd, headless=True, auto_save=False, seed=seed)
    brain.world.ensure_home()
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v90.yaml", legacy_brain=brain)
    rt.config.seed = seed
    rt.config.ticks = ticks
    result = rt.run()
    out = _repo_root() / "results" / "science_bundle" / "science_bundle_smoke.json"
    exported = export_science_bundle(rt, result, out, repo_root=_repo_root())
    return IntegratedTaskResult(
        task_id="science_bundle_smoke",
        ablation_id=ablation.ablation_id,
        seed=seed,
        primary_metrics={
            "science_bundle": 1.0 if exported.get("exported") else 0.0,
            "personal_artifacts_found": float(exported.get("personal_artifacts_found", 0)),
        },
        secondary_metrics={},
        details={"export": exported},
    )
