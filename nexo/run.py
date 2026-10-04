#!/usr/bin/env python3
"""CLI NEXO — perfiles legacy e integrado."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nexo.run")
    parser.add_argument("--config", type=Path, default=_root() / "configs/nexo/integrated_v1.yaml")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--ticks", type=int, default=None)
    parser.add_argument("--legacy", action="store_true", help="Usar InfantApeBrain legacy")
    parser.add_argument("--trace-output", type=Path, default=None, help="Exportar traza JSON integrada")
    parser.add_argument("--replication-dir", type=Path, default=None, help="Exportar paquete de replicación")
    parser.add_argument(
        "--meta-analysis-dir",
        type=Path,
        default=None,
        help="Directorio raíz de réplicas para meta-análisis JSON",
    )
    parser.add_argument(
        "--replication-batch-seeds",
        type=int,
        nargs="+",
        default=None,
        help="Exportar paquetes de replicación multi-seed",
    )
    parser.add_argument(
        "--replication-batch-dir",
        type=Path,
        default=None,
        help="Directorio raíz para batch de replicación",
    )
    parser.add_argument(
        "--legacy-bridge-output",
        type=Path,
        default=None,
        help="Exportar comparación integrado vs legacy",
    )
    parser.add_argument(
        "--pipeline-manifest",
        type=Path,
        default=None,
        help="Ejecutar pipeline integrado (batería + meta + cross)",
    )
    args = parser.parse_args(argv)

    cfg_path = args.config
    if not cfg_path.is_file():
        print(json.dumps({"error": f"config_not_found:{cfg_path}"}), file=sys.stderr)
        return 1

    data = __import__("yaml").safe_load(cfg_path.read_text(encoding="utf-8"))
    if args.legacy or data.get("mode") == "legacy_brain":
        from brain.mind import InfantApeBrain
        from brain.profile import COMPACT_PROFILE

        seed = args.seed if args.seed is not None else int(data.get("seed", 42))
        steps = args.ticks if args.ticks is not None else int(data.get("ticks", 8))
        brain = InfantApeBrain(profile=COMPACT_PROFILE, headless=True, auto_save=False, seed=seed)
        traj = []
        for _ in range(steps):
            out = brain.world_tick(steps=1)
            delib = out.get("deliberation") or {}
            traj.append(delib.get("choice_key"))
        print(json.dumps({"mode": "legacy", "seed": seed, "trajectory": traj}, indent=2))
        return 0

    from nexo.integrated_runtime import runtime_from_config

    rt = runtime_from_config(cfg_path)
    if args.seed is not None:
        rt.config.seed = args.seed
    if args.ticks is not None:
        rt.config.ticks = args.ticks
    started = time.perf_counter()
    result = rt.run()
    elapsed = time.perf_counter() - started

    trace_path = args.trace_output
    if trace_path is None:
        tracing_cfg = data.get("tracing") or {}
        cfg_trace = tracing_cfg.get("export_path")
        if cfg_trace and rt.config.tracing_mode == "integrated":
            trace_path = Path(cfg_trace)
            if not trace_path.is_absolute():
                trace_path = _root() / trace_path
    if trace_path is not None:
        result["trace_export"] = rt.export_trace(trace_path)

    replication_dir = args.replication_dir
    if replication_dir is None:
        repl_cfg = data.get("replication") or {}
        cfg_repl = repl_cfg.get("export_dir")
        if cfg_repl and rt.config.replication_mode == "integrated":
            replication_dir = Path(cfg_repl)
            if not replication_dir.is_absolute():
                replication_dir = _root() / replication_dir
    if replication_dir is not None:
        result["replication_export"] = rt.export_replication(replication_dir, result)

    meta_root = args.meta_analysis_dir
    meta_output: Path | None = None
    if meta_root is None:
        meta_cfg = data.get("meta_analysis") or {}
        cfg_meta_root = meta_cfg.get("replication_root")
        cfg_meta_output = meta_cfg.get("export_path")
        if cfg_meta_root and rt.config.meta_analysis_mode == "integrated":
            meta_root = Path(cfg_meta_root)
            if not meta_root.is_absolute():
                meta_root = _root() / meta_root
        if cfg_meta_output:
            meta_output = Path(cfg_meta_output)
            if not meta_output.is_absolute():
                meta_output = _root() / meta_output
    if meta_root is not None:
        if meta_output is None:
            meta_output = _root() / "results/meta_analysis/summary.json"
        result["meta_analysis_export"] = rt.export_meta_analysis(meta_root, meta_output)

    batch_seeds = args.replication_batch_seeds
    batch_dir = args.replication_batch_dir
    if batch_seeds is None:
        repl_cfg = data.get("replication") or {}
        if repl_cfg.get("auto_batch") and rt.config.replication_batch_mode == "integrated":
            cfg_batch_seeds = repl_cfg.get("batch_seeds")
            if cfg_batch_seeds:
                batch_seeds = [int(s) for s in cfg_batch_seeds]
        cfg_batch_dir = repl_cfg.get("batch_dir")
        if cfg_batch_dir:
            batch_dir = Path(cfg_batch_dir)
            if not batch_dir.is_absolute():
                batch_dir = _root() / batch_dir
    if batch_seeds:
        if batch_dir is None:
            batch_dir = _root() / "results/replication/batch"
        result["replication_batch_export"] = rt.export_replication_batch(
            tuple(batch_seeds),
            batch_dir,
            ticks=args.ticks,
        )

    cross_cfg = data.get("cross_battery") or {}
    cross_reports = cross_cfg.get("reports") or {}
    cross_output = cross_cfg.get("export_path")
    if cross_reports and rt.config.cross_battery_mode == "integrated":
        report_paths = {
            str(label): (Path(p) if Path(p).is_absolute() else _root() / p)
            for label, p in cross_reports.items()
        }
        out_path = Path(cross_output) if cross_output else _root() / "results/cross_battery/comparison.json"
        if not out_path.is_absolute():
            out_path = _root() / out_path
        existing = {k: v for k, v in report_paths.items() if v.is_file()}
        if len(existing) >= 2:
            result["cross_battery_export"] = rt.export_cross_battery(existing, out_path)

    bridge_path = args.legacy_bridge_output
    if bridge_path is None:
        bridge_cfg = data.get("legacy_bridge") or {}
        cfg_bridge = bridge_cfg.get("export_path")
        if bridge_cfg.get("auto_export") and cfg_bridge and rt.config.legacy_bridge_mode == "integrated":
            bridge_path = Path(cfg_bridge)
            if not bridge_path.is_absolute():
                bridge_path = _root() / bridge_path
    if bridge_path is not None:
        result["legacy_bridge_export"] = rt.export_legacy_bridge(result, bridge_path)

    pipeline_manifest = args.pipeline_manifest
    if pipeline_manifest is None:
        pipeline_cfg = data.get("pipeline") or {}
        cfg_manifest = pipeline_cfg.get("manifest")
        if pipeline_cfg.get("auto_run") and cfg_manifest and rt.config.orchestration_mode == "integrated":
            pipeline_manifest = Path(cfg_manifest)
            if not pipeline_manifest.is_absolute():
                pipeline_manifest = _root() / pipeline_manifest
    if pipeline_manifest is not None and rt.config.orchestration_mode == "integrated":
        from nexo.behavioral.orchestration import run_integrated_pipeline

        pipeline_cfg = data.get("pipeline") or {}
        meta_cfg = data.get("meta_analysis") or {}
        cross_cfg = data.get("cross_battery") or {}
        meta_root = meta_cfg.get("replication_root")
        meta_out = meta_cfg.get("export_path")
        cross_reports = cross_cfg.get("reports") or {}
        cross_out = cross_cfg.get("export_path")
        pipeline_out = pipeline_cfg.get("export_path")
        if rt.config.pipeline_paper_mode == "integrated":
            paper_pipeline_cfg = data.get("pipeline_paper") or {}
            paper_out = paper_pipeline_cfg.get("output_dir") or "results/pipeline_paper"
            paper_out_path = _root() / paper_out if not Path(paper_out).is_absolute() else Path(paper_out)
            if rt.config.latex_master_mode == "integrated":
                result["pipeline_paper_export"] = rt.run_pipeline_paper_auto(
                    pipeline_manifest,
                    paper_out_path,
                    result,
                    pipeline_output=_root() / pipeline_out if pipeline_out else None,
                    meta_root=_root() / meta_root if meta_root else None,
                    meta_output=_root() / meta_out if meta_out else None,
                    cross_reports={
                        str(k): (_root() / v) for k, v in cross_reports.items()
                    } if cross_reports else None,
                    cross_output=_root() / cross_out if cross_out else None,
                )
            else:
                result["pipeline_paper_export"] = rt.run_pipeline_paper(
                    pipeline_manifest,
                    paper_out_path,
                    pipeline_output=_root() / pipeline_out if pipeline_out else None,
                    meta_root=_root() / meta_root if meta_root else None,
                    meta_output=_root() / meta_out if meta_out else None,
                    cross_reports={
                        str(k): (_root() / v) for k, v in cross_reports.items()
                    } if cross_reports else None,
                    cross_output=_root() / cross_out if cross_out else None,
                )
        else:
            result["pipeline_export"] = run_integrated_pipeline(
                pipeline_manifest,
                meta_root=_root() / meta_root if meta_root else None,
                meta_output=_root() / meta_out if meta_out else None,
                cross_reports={
                    str(k): (_root() / v) for k, v in cross_reports.items()
                } if cross_reports else None,
                cross_output=_root() / cross_out if cross_out else None,
                pipeline_output=_root() / pipeline_out if pipeline_out else None,
            )

    scale_cfg = data.get("scale") or {}
    scale_path = scale_cfg.get("export_path")
    if scale_path and rt.config.scale_mode == "integrated":
        out_scale = Path(scale_path)
        if not out_scale.is_absolute():
            out_scale = _root() / out_scale
        result["scale_export"] = rt.export_scale_profile(result, out_scale, elapsed_seconds=elapsed)

    adapter_cfg = data.get("legacy_adapter") or {}
    adapter_path = adapter_cfg.get("export_path")
    if adapter_cfg.get("auto_export") and adapter_path and rt.config.legacy_adapter_mode == "integrated":
        out_adapter = Path(adapter_path)
        if not out_adapter.is_absolute():
            out_adapter = _root() / out_adapter
        result["legacy_adapter_export"] = rt.export_legacy_adapter_report(result, out_adapter)

    early_cfg = data.get("legacy_adapter_early") or {}
    early_path = early_cfg.get("export_path")
    if early_path and rt.config.legacy_adapter_early_mode == "integrated":
        out_early = Path(early_path)
        if not out_early.is_absolute():
            out_early = _root() / out_early
        result["legacy_adapter_early_export"] = rt.export_legacy_adapter_early(result, out_early)

    r100_cfg = data.get("roadmap100_bridge") or {}
    r100_path = r100_cfg.get("export_path")
    if r100_path and rt.config.roadmap100_bridge_mode == "integrated":
        out_r100 = Path(r100_path)
        if not out_r100.is_absolute():
            out_r100 = _root() / out_r100
        result["roadmap100_bridge_export"] = rt.export_roadmap100_bridge(result, out_r100)

    flask_cfg = data.get("flask_demo_bridge") or {}
    flask_path = flask_cfg.get("export_path")
    if flask_path and rt.config.flask_demo_bridge_mode == "integrated":
        out_flask = Path(flask_path)
        if not out_flask.is_absolute():
            out_flask = _root() / out_flask
        result["flask_demo_bridge_export"] = rt.export_flask_demo_bridge(result, out_flask)

    w3d_cfg = data.get("world3d_sync") or {}
    w3d_path = w3d_cfg.get("export_path")
    if w3d_path and rt.config.world3d_sync_mode == "integrated":
        out_w3d = Path(w3d_path)
        if not out_w3d.is_absolute():
            out_w3d = _root() / out_w3d
        result["world3d_sync_export"] = rt.export_world3d_sync(result, out_w3d)

    auto_cfg = data.get("autonomy_guard") or {}
    auto_path = auto_cfg.get("export_path")
    if auto_path and rt.config.autonomy_guard_mode == "integrated":
        out_auto = Path(auto_path)
        if not out_auto.is_absolute():
            out_auto = _root() / out_auto
        result["autonomy_guard_export"] = rt.export_autonomy_guard(result, out_auto)

    hypo_cfg = data.get("hypothalamus_multimodal") or {}
    hypo_path = hypo_cfg.get("export_path")
    if hypo_path and rt.config.hypothalamus_multimodal_mode == "integrated":
        out_hypo = Path(hypo_path)
        if not out_hypo.is_absolute():
            out_hypo = _root() / out_hypo
        result["hypothalamus_multimodal_export"] = rt.export_hypothalamus_multimodal(result, out_hypo)

    comp_cfg = data.get("companion_integrated") or {}
    comp_path = comp_cfg.get("export_path")
    if comp_path and rt.config.companion_integrated_mode == "integrated":
        out_comp = Path(comp_path)
        if not out_comp.is_absolute():
            out_comp = _root() / out_comp
        result["companion_integrated_export"] = rt.export_companion_integrated(result, out_comp)

    motor_cfg = data.get("unified_motor") or {}
    motor_path = motor_cfg.get("export_path")
    if motor_path and rt.config.unified_motor_mode == "integrated":
        out_motor = Path(motor_path)
        if not out_motor.is_absolute():
            out_motor = _root() / out_motor
        result["unified_motor_export"] = rt.export_unified_motor(result, out_motor)

    als_cfg = data.get("agent_loop_sync") or {}
    als_path = als_cfg.get("export_path")
    if als_path and rt.config.agent_loop_sync_mode == "integrated":
        out_als = Path(als_path)
        if not out_als.is_absolute():
            out_als = _root() / out_als
        result["agent_loop_sync_export"] = rt.export_agent_loop_sync(result, out_als)

    mem_cfg = data.get("memory_bridge") or {}
    mem_path = mem_cfg.get("export_path")
    if mem_path and rt.config.memory_bridge_mode == "integrated":
        out_mem = Path(mem_path)
        if not out_mem.is_absolute():
            out_mem = _root() / out_mem
        result["memory_bridge_export"] = rt.export_memory_bridge(result, out_mem)

    eblock_cfg = data.get("roadmap100_e_block") or {}
    eblock_path = eblock_cfg.get("export_path")
    if eblock_path and rt.config.roadmap100_e_block_mode == "integrated":
        out_eblock = Path(eblock_path)
        if not out_eblock.is_absolute():
            out_eblock = _root() / out_eblock
        result["roadmap100_e_block_export"] = rt.export_roadmap100_e_block(result, out_eblock)

    unif_cfg = data.get("memory_unification") or {}
    unif_path = unif_cfg.get("export_path")
    if unif_path and rt.config.memory_unification_mode == "integrated":
        out_unif = Path(unif_path)
        if not out_unif.is_absolute():
            out_unif = _root() / out_unif
        result["memory_unification_export"] = rt.export_memory_unification(result, out_unif)

    cert_cfg = data.get("causal_certificate") or {}
    cert_path = cert_cfg.get("export_path")
    if cert_path and rt.config.causal_certificate_mode == "integrated":
        out_cert = Path(cert_path)
        if not out_cert.is_absolute():
            out_cert = _root() / out_cert
        result["causal_certificate_export"] = rt.export_causal_certificate(result, out_cert)

    dil_cfg = data.get("day_in_the_life") or {}
    dil_path = dil_cfg.get("export_path")
    if dil_path and rt.config.day_in_the_life_mode == "integrated":
        out_dil = Path(dil_path)
        if not out_dil.is_absolute():
            out_dil = _root() / out_dil
        result["day_in_the_life_export"] = rt.export_day_in_the_life(result, out_dil)

    audit_cfg = data.get("agency_audit") or {}
    audit_path = audit_cfg.get("export_path")
    if audit_path and rt.config.agency_audit_mode == "integrated":
        out_audit = Path(audit_path)
        if not out_audit.is_absolute():
            out_audit = _root() / out_audit
        result["agency_audit_export"] = rt.export_agency_audit(result, out_audit)

    science_cfg = data.get("science_bundle") or {}
    science_path = science_cfg.get("export_path")
    if science_path and rt.config.science_bundle_mode == "integrated":
        out_science = Path(science_path)
        if not out_science.is_absolute():
            out_science = _root() / out_science
        result["science_bundle_export"] = rt.export_science_bundle(result, out_science)

    delib_cfg = data.get("deliberation_bridge") or {}
    delib_path = delib_cfg.get("export_path")
    if delib_path and rt.config.deliberation_bridge_mode == "integrated":
        out_delib = Path(delib_path)
        if not out_delib.is_absolute():
            out_delib = _root() / out_delib
        result["deliberation_bridge_export"] = rt.export_deliberation_bridge(result, out_delib)

    fusion_cfg = data.get("deliberation_fusion") or {}
    fusion_path = fusion_cfg.get("export_path")
    if fusion_path and rt.config.deliberation_fusion_mode == "integrated":
        out_fusion = Path(fusion_path)
        if not out_fusion.is_absolute():
            out_fusion = _root() / out_fusion
        result["deliberation_fusion_export"] = rt.export_deliberation_fusion(result, out_fusion)

    unified_cfg = data.get("deliberation_unified") or {}
    unified_path = unified_cfg.get("export_path")
    if unified_path and rt.config.deliberation_unified_mode == "integrated":
        out_unified = Path(unified_path)
        if not out_unified.is_absolute():
            out_unified = _root() / out_unified
        result["deliberation_unified_export"] = rt.export_deliberation_unified(result, out_unified)

    weight_cfg = data.get("deliberation_weight") or {}
    weight_path = weight_cfg.get("export_path")
    if weight_path and rt.config.deliberation_weight_mode == "integrated":
        out_weight = Path(weight_path)
        if not out_weight.is_absolute():
            out_weight = _root() / out_weight
        result["deliberation_weight_export"] = rt.export_deliberation_weight(result, out_weight)

    lif_cfg = data.get("lif_scale") or {}
    lif_path = lif_cfg.get("export_path")
    if lif_path and rt.config.lif_scale_mode == "integrated":
        out_lif = Path(lif_path)
        if not out_lif.is_absolute():
            out_lif = _root() / out_lif
        result["lif_scale_export"] = rt.export_lif_scale_probe(
            out_lif,
            profile_key=str(lif_cfg.get("profile_key", "compact")),
            ticks=int(lif_cfg.get("ticks", 2)),
            run_bench=bool(lif_cfg.get("run_bench", False)),
        )

    gpu_cfg = data.get("gpu_bench") or {}
    gpu_path = gpu_cfg.get("export_path")
    if gpu_path and rt.config.gpu_bench_mode == "integrated":
        out_gpu = Path(gpu_path)
        if not out_gpu.is_absolute():
            out_gpu = _root() / out_gpu
        result["gpu_bench_export"] = rt.export_gpu_bench(
            out_gpu,
            profile_key=str(gpu_cfg.get("profile_key", "compact")),
            ticks=int(gpu_cfg.get("ticks", 1)),
            ci_safe=bool(gpu_cfg.get("ci_safe", True)),
        )

    pub_cfg = data.get("publication") or {}
    pub_dir = pub_cfg.get("export_dir")
    paper_cfg = data.get("paper_pack") or {}
    paper_dir = paper_cfg.get("export_dir")
    battery_paper_cfg = data.get("battery_paper") or {}
    battery_paper_dir_cfg = battery_paper_cfg.get("export_dir")
    full_pub_cfg = data.get("full_publication") or {}

    out_paper: Path | None = None
    if paper_dir and rt.config.paper_pack_mode == "integrated":
        out_paper = Path(paper_dir)
        if not out_paper.is_absolute():
            out_paper = _root() / out_paper
        result["paper_pack_export"] = rt.export_paper_pack(result, out_paper)

    out_battery_paper: Path | None = None
    battery_reports = battery_paper_cfg.get("reports") or {}
    if battery_paper_dir_cfg and rt.config.battery_paper_mode == "integrated" and battery_reports:
        out_battery_paper = Path(battery_paper_dir_cfg)
        if not out_battery_paper.is_absolute():
            out_battery_paper = _root() / out_battery_paper
        report_paths = {str(k): (_root() / v if not Path(v).is_absolute() else Path(v)) for k, v in battery_reports.items()}
        result["battery_paper_export"] = rt.export_battery_paper(report_paths, out_battery_paper)

    figures_cfg = data.get("paper_figures") or {}
    figures_report = figures_cfg.get("report_path")
    figures_dir = figures_cfg.get("export_dir")
    out_fig: Path | None = None
    if figures_dir and rt.config.paper_figures_mode == "integrated" and figures_report:
        out_fig = Path(figures_dir)
        if not out_fig.is_absolute():
            out_fig = _root() / out_fig
        report_fig = Path(figures_report)
        if not report_fig.is_absolute():
            report_fig = _root() / report_fig
        result["paper_figures_export"] = rt.export_paper_figures(report_fig, out_fig)

    if pub_dir and rt.config.publication_mode == "integrated":
        out_pub = Path(pub_dir)
        if not out_pub.is_absolute():
            out_pub = _root() / out_pub
        artifacts: dict[str, Path] = {}
        scale_export = result.get("scale_export") or {}
        if scale_export.get("path"):
            artifacts["scale"] = Path(scale_export["path"])
        result["publication_export"] = rt.export_publication_bundle(result, out_pub, artifact_paths=artifacts)

    full_pub_dir = full_pub_cfg.get("export_dir")
    if full_pub_dir and rt.config.full_publication_mode == "integrated":
        out_full = Path(full_pub_dir)
        if not out_full.is_absolute():
            out_full = _root() / out_full
        artifacts_full: dict[str, Path] = {}
        scale_export = result.get("scale_export") or {}
        if scale_export.get("path"):
            artifacts_full["scale"] = Path(scale_export["path"])
        result["full_publication_export"] = rt.export_full_publication_bundle(
            result,
            out_full,
            artifact_paths=artifacts_full,
            paper_pack_dir=out_paper,
            battery_paper_dir=out_battery_paper,
            figures_dir=out_fig,
        )

    paper_pipeline_cfg = data.get("pipeline_paper") or {}
    if (
        paper_pipeline_cfg.get("auto_run")
        and rt.config.pipeline_paper_mode == "integrated"
        and "pipeline_paper_export" not in result
    ):
        pp_manifest = paper_pipeline_cfg.get("manifest") or (data.get("pipeline") or {}).get("manifest")
        if pp_manifest:
            pp_manifest_path = Path(pp_manifest)
            if not pp_manifest_path.is_absolute():
                pp_manifest_path = _root() / pp_manifest_path
            paper_out = paper_pipeline_cfg.get("output_dir") or "results/pipeline_paper"
            paper_out_path = _root() / paper_out if not Path(paper_out).is_absolute() else Path(paper_out)
            pipeline_cfg = data.get("pipeline") or {}
            meta_cfg = data.get("meta_analysis") or {}
            cross_cfg = data.get("cross_battery") or {}
            result["pipeline_paper_export"] = rt.run_pipeline_paper_auto(
                pp_manifest_path,
                paper_out_path,
                result,
                pipeline_output=_root() / pipeline_cfg["export_path"] if pipeline_cfg.get("export_path") else None,
                meta_root=_root() / meta_cfg["replication_root"] if meta_cfg.get("replication_root") else None,
                meta_output=_root() / meta_cfg["export_path"] if meta_cfg.get("export_path") else None,
                cross_reports={
                    str(k): (_root() / v) for k, v in (cross_cfg.get("reports") or {}).items()
                } if cross_cfg.get("reports") else None,
                cross_output=_root() / cross_cfg["export_path"] if cross_cfg.get("export_path") else None,
            )

    latex_cfg = data.get("latex_master") or {}
    latex_dir = latex_cfg.get("export_dir")
    if latex_dir and rt.config.latex_master_mode == "integrated":
        out_latex = Path(latex_dir)
        if not out_latex.is_absolute():
            out_latex = _root() / out_latex
        result["latex_master_export"] = rt.export_latex_master(
            result,
            out_latex,
            paper_pack_dir=out_paper,
            battery_paper_dir=out_battery_paper,
            figures_dir=out_fig,
        )

    battery_full_cfg = data.get("battery_full") or {}
    battery_full_dir = battery_full_cfg.get("export_dir")
    bf_manifest = battery_full_cfg.get("manifest")
    if battery_full_dir and bf_manifest and rt.config.battery_full_mode == "integrated":
        out_bf = Path(battery_full_dir)
        if not out_bf.is_absolute():
            out_bf = _root() / out_bf
        bf_path = Path(bf_manifest)
        if not bf_path.is_absolute():
            bf_path = _root() / bf_path
        result["battery_full_export"] = rt.run_battery_full(bf_path, out_bf)

    release_cfg = data.get("release_bundle") or {}
    release_dir = release_cfg.get("export_dir")
    if release_dir and rt.config.release_bundle_mode == "integrated":
        out_rel = Path(release_dir)
        if not out_rel.is_absolute():
            out_rel = _root() / out_rel
        roots: dict[str, Path] = {}
        if out_paper and out_paper.is_dir():
            roots["paper_pack"] = out_paper
        if out_battery_paper and out_battery_paper.is_dir():
            roots["battery_paper"] = out_battery_paper
        if out_fig and out_fig.is_dir():
            roots["figures"] = out_fig
        full_pub = full_pub_cfg.get("export_dir")
        if full_pub:
            fp = Path(full_pub)
            if not fp.is_absolute():
                fp = _root() / fp
            if fp.is_dir():
                roots["full_publication"] = fp
        result["release_bundle_export"] = rt.export_release_bundle(
            result,
            out_rel,
            artifact_roots=roots,
            config_path=str(cfg_path),
        )

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
