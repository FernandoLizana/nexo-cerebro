"""Paired run validation and delta computation."""

from __future__ import annotations

from typing import Any

from nexo_qa.chaos.models import ChaosPairPlan, PairedChaosDelta, PairValidity
from nexo_qa.population.models import RunExecutionRecord, RunPlan, RunStatus


def validate_pair_invariants(
    baseline: RunPlan,
    perturbed: RunPlan,
    *,
    baseline_rec: RunExecutionRecord | None = None,
    perturbed_rec: RunExecutionRecord | None = None,
) -> tuple[PairValidity, str | None]:
    if baseline.task_id != perturbed.task_id:
        return "INVALID_PAIR", "task mismatch"
    if baseline.persona_id != perturbed.persona_id:
        return "INVALID_PAIR", "persona mismatch"
    if baseline.seed != perturbed.seed:
        return "INVALID_PAIR", "seed mismatch"
    if baseline.condition_set_id == perturbed.condition_set_id:
        return "INVALID_PAIR", "condition must differ"
    b_metrics = (baseline.config_versions or {}).get("metrics")
    p_metrics = (perturbed.config_versions or {}).get("metrics")
    if b_metrics and p_metrics and b_metrics != p_metrics:
        return "INCOMPATIBLE_PAIR", "metric version mismatch"
    if baseline_rec and baseline_rec.status != RunStatus.COMPLETED:
        return "INVALID_PAIR", "baseline not completed"
    if perturbed_rec and perturbed_rec.status != RunStatus.COMPLETED:
        return "INVALID_PAIR", "perturbed not completed"
    if perturbed_rec and perturbed_rec.p6_summary:
        inj = (perturbed_rec.p6_summary.get("perturbation_coverage") or {}).get("successfully_injected", 0)
        if inj < 1 and perturbed.perturbation_id:
            return "INVALID_PAIR", "perturbation not injected"
    return "VALID", None


def _metric_value(summary: dict[str, Any] | None, key: str) -> float | None:
    if not summary:
        return None
    block = summary.get(key) or {}
    val = block.get("value") if isinstance(block, dict) else None
    return None if val is None else float(val)


def _status(summary: dict[str, Any] | None) -> str:
    if not summary:
        return "UNKNOWN"
    return str(summary.get("assessment_status", "UNKNOWN"))


def compute_paired_delta(
    pair: ChaosPairPlan,
    baseline_rec: RunExecutionRecord,
    perturbed_rec: RunExecutionRecord,
    *,
    validity: PairValidity | None = None,
    invalid_reason: str | None = None,
) -> PairedChaosDelta:
    validity = validity or validate_pair_invariants(
        baseline_rec.plan, perturbed_rec.plan, baseline_rec=baseline_rec, perturbed_rec=perturbed_rec
    )[0]
    if invalid_reason is None and validity != "VALID":
        invalid_reason = validate_pair_invariants(
            baseline_rec.plan, perturbed_rec.plan, baseline_rec=baseline_rec, perturbed_rec=perturbed_rec
        )[1]

    b_sum = baseline_rec.p6_summary or {}
    p_sum = perturbed_rec.p6_summary or {}
    metric_deltas: dict[str, float | None] = {}
    if validity == "VALID":
        for key in ("ncfs", "ehfp", "crs"):
            bv = _metric_value(b_sum, key)
            pv = _metric_value(p_sum, key)
            if bv is not None and pv is not None:
                metric_deltas[f"{key}_delta"] = round(pv - bv, 4)
            else:
                metric_deltas[f"{key}_delta"] = None

    b_status = _status(b_sum)
    p_status = _status(p_sum)
    status_change = f"{b_status} → {p_status}" if validity == "VALID" else None

    b_failures = len(b_sum.get("top_issues") or [])
    p_failures = len(p_sum.get("top_issues") or [])
    failure_deltas = {"failure_count_delta": p_failures - b_failures} if validity == "VALID" else {}

    recovery = None
    interruption_ticks = None
    if validity == "VALID":
        recovery_block = p_sum.get("interruption_recovery") or {}
        interruption_ticks = recovery_block.get("ticks_to_progress")
        crs_b = _metric_value(b_sum, "crs")
        crs_p = _metric_value(p_sum, "crs")
        if crs_b is not None and crs_p is not None:
            recovery = round(crs_p - crs_b, 4)

    return PairedChaosDelta(
        pair_id=pair.pair_id,
        validity=validity,
        baseline_run_id=baseline_rec.plan.run_id,
        perturbed_run_id=perturbed_rec.plan.run_id,
        metric_deltas=metric_deltas,
        failure_deltas=failure_deltas,
        status_change=status_change,
        recovery_delta=recovery,
        interruption_recovery_ticks=interruption_ticks,
        artifact_refs={
            "baseline_summary": baseline_rec.summary_path or "",
            "perturbed_summary": perturbed_rec.summary_path or "",
        },
        invalid_reason=invalid_reason,
    )


def status_degradation_rate(deltas: list[PairedChaosDelta]) -> dict[str, Any]:
    valid = [d for d in deltas if d.validity == "VALID"]
    degraded = 0
    baseline_success = 0
    for d in valid:
        if not d.status_change or "→" not in d.status_change:
            continue
        b, p = [s.strip() for s in d.status_change.split("→", 1)]
        if b.startswith("PASS"):
            baseline_success += 1
            if not p.startswith("PASS"):
                degraded += 1
    return {
        "valid_pairs": len(valid),
        "baseline_successful": baseline_success,
        "status_degradation_count": degraded,
        "status_degradation_rate": round(degraded / max(1, baseline_success), 4),
        "denominator": baseline_success,
    }
