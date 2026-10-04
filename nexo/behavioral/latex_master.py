"""Manifiesto LaTeX maestro compilable (Sprint 47)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_if_exists(path: Path) -> str:
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return ""


def build_latex_master_body(
    *,
    profile: str,
    paper_pack_dir: Path | None = None,
    battery_paper_dir: Path | None = None,
    figures_dir: Path | None = None,
) -> str:
    sections: list[str] = [
        f"% NEXO Integrated Brain — LaTeX master ({profile})",
        "\\documentclass[11pt]{article}",
        "\\usepackage[utf8]{inputenc}",
        "\\usepackage[T1]{fontenc}",
        "\\usepackage{graphicx}",
        "\\usepackage{booktabs}",
        "\\usepackage{hyperref}",
        "\\title{NEXO Integrated Brain --- Reproducibility Report}",
        f"\\author{{Profile: {profile}}}",
        "\\date{\\today}",
        "\\begin{document}",
        "\\maketitle",
        "\\section{Run Metrics}",
    ]
    metrics_tex = ""
    if paper_pack_dir is not None:
        metrics_tex = _read_if_exists(paper_pack_dir / "metrics_table.tex")
    if metrics_tex.strip():
        sections.append(metrics_tex)
    else:
        sections.append("\\emph{No metrics table exported.}")

    sections.append("\\section{Battery Summary}")
    battery_tex = ""
    if battery_paper_dir is not None:
        for tex in sorted(battery_paper_dir.glob("*_battery.tex")):
            battery_tex += _read_if_exists(tex) + "\n"
    if battery_tex.strip():
        sections.append(battery_tex)
    else:
        sections.append("\\emph{No battery tables exported.}")

    sections.append("\\section{Figures}")
    if figures_dir is not None and (figures_dir / "battery_scores.svg").is_file():
        sections.extend([
            "\\begin{figure}[h]",
            "  \\centering",
            f"  \\includegraphics[width=0.85\\linewidth]{{{figures_dir.name}/battery_scores.svg}}",
            "  \\caption{Integrated battery task scores (SVG; use \\texttt{pdflatex + svg} or convert).}",
            "\\end{figure}",
            _read_if_exists(figures_dir / "figure_battery.tex"),
        ])
    else:
        sections.append("\\emph{No figures exported.}")

    sections.extend(["\\end{document}", ""])
    return "\n".join(sections)


def export_latex_master(
    result: dict[str, Any],
    output_dir: Path,
    *,
    paper_pack_dir: Path | None = None,
    battery_paper_dir: Path | None = None,
    figures_dir: Path | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    profile = str(result.get("profile", "integrated"))
    master = build_latex_master_body(
        profile=profile,
        paper_pack_dir=paper_pack_dir,
        battery_paper_dir=battery_paper_dir,
        figures_dir=figures_dir,
    )
    master_path = output_dir / "nexo_integrated_master.tex"
    master_path.write_text(master, encoding="utf-8")
    manifest = {
        "profile": profile,
        "master_tex": str(master_path),
        "inputs": {
            "paper_pack": str(paper_pack_dir) if paper_pack_dir else None,
            "battery_paper": str(battery_paper_dir) if battery_paper_dir else None,
            "figures": str(figures_dir) if figures_dir else None,
        },
    }
    manifest_path = output_dir / "latex_master_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "exported": True,
        "output_dir": str(output_dir),
        "master_tex": str(master_path),
        "manifest": str(manifest_path),
    }
