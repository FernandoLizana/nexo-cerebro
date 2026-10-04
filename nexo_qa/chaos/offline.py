"""Offline paired chaos analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nexo_qa.chaos.models import ChaosPlan, PairedChaosDelta
from nexo_qa.chaos.pairs import compute_paired_delta
from nexo_qa.chaos.runner import ChaosState


def analyze_pairs(
    *,
    plan: ChaosPlan,
    state: ChaosState,
) -> tuple[list[PairedChaosDelta], dict[str, Any]]:
    deltas: list[PairedChaosDelta] = []
    injection = {"planned": 0, "successfully_injected": 0, "missed": 0, "injection_failures": 0}
    for pair in plan.pairs:
        baseline_rec = state.records.get(pair.baseline_run_id)
        perturbed_rec = state.records.get(pair.perturbed_run_id)
        if baseline_rec is None or perturbed_rec is None:
            deltas.append(
                PairedChaosDelta(
                    pair_id=pair.pair_id,
                    validity="INVALID_PAIR",
                    baseline_run_id=pair.baseline_run_id,
                    perturbed_run_id=pair.perturbed_run_id,
                    invalid_reason="missing run record",
                )
            )
            continue
        delta = compute_paired_delta(pair, baseline_rec, perturbed_rec)
        deltas.append(delta)
        cov = (perturbed_rec.p6_summary or {}).get("perturbation_coverage") or {}
        injection["planned"] += cov.get("planned", 1)
        injection["successfully_injected"] += cov.get("successfully_injected", 0)
        injection["missed"] += cov.get("missed", 0)
        injection["injection_failures"] += cov.get("injection_failures", 0)
    return deltas, injection


def analyze_chaos_directory(chaos_root: Path | str) -> dict[str, Any]:
    root = Path(chaos_root)
    plan = _load_plan(root / "chaos_plan.json")
    state = ChaosState.load_json(root / "chaos_state.json")
    deltas, injection = analyze_pairs(plan=plan, state=state)
    from nexo_qa.chaos.reporting import build_chaos_report, write_chaos_report_json, write_paired_csv

    report = build_chaos_report(
        chaos_id=plan.chaos_id,
        plan=plan,
        state=state,
        deltas=deltas,
        injection_coverage=injection,
    )
    write_chaos_report_json(root / "chaos_report.json", report)
    write_paired_csv(root / "paired_results.csv", deltas)
    return report


def _load_plan(path: Path) -> ChaosPlan:
    import json

    from nexo_qa.chaos.models import ChaosPairPlan, PerturbationSpec
    from nexo_qa.population.models import RunPlan

    data = json.loads(path.read_text(encoding="utf-8"))
    pairs = tuple(
        ChaosPairPlan(
            pair_id=p["pair_id"],
            perturbation=PerturbationSpec.from_dict(p["perturbation"]),
            baseline_run_id=p["baseline_run_id"],
            perturbed_run_id=p["perturbed_run_id"],
            task_id=p["task_id"],
            persona_id=p["persona_id"],
            seed=int(p["seed"]),
            condition_perturbed=p.get("condition_perturbed", ""),
        )
        for p in data.get("pairs") or []
    )
    runs = tuple(RunPlan.from_dict(r) for r in data.get("runs") or [])
    return ChaosPlan(
        chaos_id=str(data["chaos_id"]),
        spec_hash=str(data.get("spec_hash", "")),
        pairs=pairs,
        runs=runs,
    )
