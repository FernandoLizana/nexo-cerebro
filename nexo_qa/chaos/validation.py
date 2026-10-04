"""Perturbation spec validation."""

from __future__ import annotations

from nexo_qa.chaos.models import ChaosSpec, PerturbationSpec, PerturbationType

SUPPORTED_TYPES: tuple[PerturbationType, ...] = (
    "INTERRUPTION",
    "LATENCY",
    "TRANSIENT_ERROR",
    "SESSION_EXPIRY",
    "VISUAL_CHANGE",
    "MODAL_DISTRACTION",
    "CONTENT_SHIFT",
    "FEEDBACK_DELAY",
    "CONTROL_DISABLE",
    "NETWORK_LIKE_FAILURE",
)

IMPLEMENTED_TYPES: tuple[PerturbationType, ...] = (
    "INTERRUPTION",
    "LATENCY",
    "TRANSIENT_ERROR",
    "SESSION_EXPIRY",
    "VISUAL_CHANGE",
    "MODAL_DISTRACTION",
    "FEEDBACK_DELAY",
    "CONTROL_DISABLE",
)


def validate_perturbation_spec(spec: PerturbationSpec) -> list[str]:
    errors: list[str] = []
    if not spec.perturbation_id:
        errors.append("perturbation_id required")
    if spec.type not in SUPPORTED_TYPES:
        errors.append(f"unsupported type {spec.type}")
    if spec.duration_ticks < 0:
        errors.append("duration_ticks must be >= 0")
    if spec.target_scope != "environment":
        errors.append("target_scope must be environment (no direct cognitive mutation)")
    trig = spec.trigger
    if trig.kind == "AT_TICK" and trig.at_tick is None:
        errors.append(f"{spec.perturbation_id}: AT_TICK requires at_tick")
    if trig.kind == "AFTER_ACTION" and trig.after_action_count is None:
        errors.append(f"{spec.perturbation_id}: AFTER_ACTION requires after_action_count")
    if trig.kind == "PROBABILISTIC_SEEDED" and (spec.seed is None and trig.probability is None):
        errors.append(f"{spec.perturbation_id}: probabilistic trigger requires seed")
    return errors


def validate_chaos_spec(spec: ChaosSpec) -> list[str]:
    errors: list[str] = []
    if not spec.chaos_id:
        errors.append("chaos_id required")
    if not spec.perturbations:
        errors.append("at least one perturbation required")
    if len(spec.perturbations) > 20:
        errors.append("chaos explosion guard: >20 perturbations")
    for p in spec.perturbations:
        errors.extend(validate_perturbation_spec(p))
    return errors
