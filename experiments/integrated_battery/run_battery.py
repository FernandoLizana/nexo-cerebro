"""Ejecutor de batería conductual integrada."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nexo.ablation.profiles import ABLATION_REGISTRY, list_ablations
from nexo.behavioral.benchmark import export_benchmark
from nexo.behavioral.task_registry import DEFAULT_BATTERY_TASKS, resolve_task_runners
from nexo.interventions.profiles import LESION_REGISTRY


def run_integrated_battery(
    *,
    seeds: tuple[int, ...] = (42, 99),
    ablation_ids: tuple[str, ...] | None = None,
    lesion_ids: tuple[str, ...] | None = None,
    task_ids: tuple[str, ...] | None = None,
    latency_mode: str = "legacy",
    routing_mode: str = "legacy",
) -> list[dict[str, Any]]:
    ablations = (
        [ABLATION_REGISTRY[a] for a in ablation_ids if a in ABLATION_REGISTRY]
        if ablation_ids
        else list_ablations()
    )
    lesions = (
        [lid for lid in (lesion_ids or ("lesion_none",)) if lid in LESION_REGISTRY or lid == "lesion_none"]
    )
    if not lesions:
        lesions = ["lesion_none"]
    runners = resolve_task_runners(task_ids or DEFAULT_BATTERY_TASKS)

    results: list[dict[str, Any]] = []
    for ablation in ablations:
        for lesion_id in lesions:
            for seed in seeds:
                for runner in runners:
                    res = runner(
                        ablation=ablation,
                        seed=seed,
                        lesion_profile=lesion_id,
                        latency_mode=latency_mode,
                        routing_mode=routing_mode,
                    )
                    results.append(res.to_dict())
    return results


def write_battery_report(results: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="experiments.integrated_battery.run_battery")
    parser.add_argument("--output", type=Path, default=Path("results/integrated_battery/report.json"))
    parser.add_argument("--benchmark", type=Path, default=None, help="Exporta JSON+CSV agregado")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 99])
    parser.add_argument("--ablations", nargs="*", default=None)
    parser.add_argument("--lesions", nargs="*", default=None)
    parser.add_argument("--tasks", nargs="*", default=None)
    parser.add_argument(
        "--latency-mode",
        choices=("legacy", "integrated"),
        default="legacy",
    )
    args = parser.parse_args(argv)
    results = run_integrated_battery(
        seeds=tuple(args.seeds),
        ablation_ids=tuple(args.ablations) if args.ablations else None,
        lesion_ids=tuple(args.lesions) if args.lesions else None,
        task_ids=tuple(args.tasks) if args.tasks else None,
        latency_mode=args.latency_mode,
    )
    write_battery_report(results, args.output)
    summary = None
    if args.benchmark is not None:
        csv_path = args.benchmark.with_suffix(".csv")
        summary = export_benchmark(results, args.benchmark, csv_path=csv_path)
    print(
        json.dumps(
            {
                "tasks": len(results),
                "output": str(args.output),
                "benchmark": str(args.benchmark) if args.benchmark else None,
                "summary_groups": summary["groups"] if summary else None,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
