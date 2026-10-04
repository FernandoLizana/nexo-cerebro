"""Manifiesto YAML reproducible para batería integrada."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from nexo.behavioral.benchmark import export_benchmark
from nexo.behavioral.comparison import compare_to_baseline, export_comparison
from nexo.behavioral.statistics import export_statistics
from nexo.behavioral.task_registry import DEFAULT_BATTERY_TASKS, resolve_task_runners
from nexo.integrated_runtime import _repo_root


@dataclass(frozen=True)
class BatteryManifest:
    name: str
    version: int
    profile: str
    seeds: tuple[int, ...]
    ablations: tuple[str, ...]
    lesions: tuple[str, ...]
    tasks: tuple[str, ...]
    latency_mode: str
    routing_mode: str
    statistics_mode: str
    permutation_mode: str
    correction_mode: str
    inference_mode: str
    hierarchical_inference_mode: str
    export_json: Path | None
    export_benchmark: Path | None
    export_comparison: Path | None
    export_statistics: Path | None

    @classmethod
    def from_yaml(cls, path: Path) -> BatteryManifest:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        root = _repo_root()
        export = data.get("export") or {}

        def _resolve(key: str) -> Path | None:
            val = export.get(key)
            if not val:
                return None
            p = Path(val)
            return p if p.is_absolute() else root / p

        task_ids = data.get("tasks")
        if isinstance(task_ids, list) and task_ids and isinstance(task_ids[0], dict):
            tasks = tuple(str(t["id"]) for t in task_ids)
        elif isinstance(task_ids, list):
            tasks = tuple(str(t) for t in task_ids)
        else:
            tasks = DEFAULT_BATTERY_TASKS

        return cls(
            name=str(data.get("name", path.stem)),
            version=int(data.get("version", 1)),
            profile=str(data.get("profile", "integrated_v12")),
            seeds=tuple(int(s) for s in data.get("seeds", [42])),
            ablations=tuple(str(a) for a in data.get("ablations", ["integrated_full"])),
            lesions=tuple(str(l) for l in data.get("lesions", ["lesion_none"])),
            tasks=tasks,
            latency_mode=str(data.get("latency_mode", "legacy")),
            routing_mode=str(data.get("routing_mode", "legacy")),
            statistics_mode=str(data.get("statistics_mode", "legacy")),
            permutation_mode=str(data.get("permutation_mode", "legacy")),
            correction_mode=str(data.get("correction_mode", "legacy")),
            inference_mode=str(data.get("inference_mode", "legacy")),
            hierarchical_inference_mode=str(data.get("hierarchical_inference_mode", "legacy")),
            export_json=_resolve("json"),
            export_benchmark=_resolve("benchmark"),
            export_comparison=_resolve("comparison"),
            export_statistics=_resolve("statistics"),
        )


def run_battery_manifest(manifest: BatteryManifest) -> list[dict[str, Any]]:
    from nexo.ablation.profiles import ABLATION_REGISTRY
    from nexo.interventions.profiles import LESION_REGISTRY

    ablations = [ABLATION_REGISTRY[a] for a in manifest.ablations if a in ABLATION_REGISTRY]
    lesions = [l for l in manifest.lesions if l in LESION_REGISTRY or l == "lesion_none"]
    if not lesions:
        lesions = ["lesion_none"]
    runners = resolve_task_runners(manifest.tasks)

    results: list[dict[str, Any]] = []
    for ablation in ablations:
        for lesion_id in lesions:
            for seed in manifest.seeds:
                for runner in runners:
                    res = runner(
                        ablation=ablation,
                        seed=seed,
                        lesion_profile=lesion_id,
                        latency_mode=manifest.latency_mode,
                        routing_mode=manifest.routing_mode,
                    )
                    results.append(res.to_dict())
    return results


def execute_manifest(path: Path) -> dict[str, Any]:
    manifest = BatteryManifest.from_yaml(path)
    results = run_battery_manifest(manifest)
    summary: dict[str, Any] = {
        "manifest": manifest.name,
        "total_runs": len(results),
        "tasks": list(manifest.tasks),
    }

    if manifest.export_json:
        manifest.export_json.parent.mkdir(parents=True, exist_ok=True)
        manifest.export_json.write_text(
            __import__("json").dumps(results, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        summary["json"] = str(manifest.export_json)

    if manifest.export_benchmark:
        bench = export_benchmark(
            results,
            manifest.export_benchmark,
            csv_path=manifest.export_benchmark.with_suffix(".csv"),
        )
        summary["benchmark_groups"] = bench["groups"]

    if manifest.export_comparison:
        comparisons = compare_to_baseline(results)
        comp = export_comparison(comparisons, manifest.export_comparison)
        summary["comparison_entries"] = comp["n_entries"]
        summary["ranking"] = comp["ranking"]

    if manifest.export_statistics and manifest.statistics_mode == "integrated":
        stats = export_statistics(
            results,
            manifest.export_statistics,
            include_permutation=manifest.permutation_mode == "integrated",
            include_fdr_correction=manifest.correction_mode == "integrated",
            include_inference=manifest.inference_mode == "integrated",
            include_hierarchical=manifest.hierarchical_inference_mode == "integrated",
        )
        summary["statistics_aggregates"] = len(stats.get("aggregates", []))
        summary["statistics_effects"] = len(stats.get("effect_sizes", []))
        summary["fdr_correction"] = stats.get("fdr_correction_enabled", False)
        summary["inference_enabled"] = stats.get("inference_enabled", False)
        summary["hierarchical_inference"] = stats.get("hierarchical_inference_enabled", False)

    return summary
