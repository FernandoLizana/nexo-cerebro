#!/usr/bin/env python3
"""Empirical figures from real CSV only; schematic architecture separately labeled."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

PF = Path(__file__).resolve().parents[1]
ROOT = PF.parent


def abc_paths() -> tuple[Path, Path, Path, int]:
    """Prefer n20_compact; return (A, B, C, n_seeds_label)."""
    n20 = PF / "raw_results" / "n20_compact"
    a = n20 / "baselines_A" / "seed_summaries.csv"
    if a.exists():
        return (
            a,
            n20 / "agency_break_B" / "seed_summaries.csv",
            n20 / "env_shift_C" / "env_shift_seed_results.csv",
            20,
        )
    return (
        PF / "raw_results" / "baselines_A" / "seed_summaries.csv",
        PF / "raw_results" / "agency_break_B" / "seed_summaries.csv",
        PF / "raw_results" / "env_shift_C" / "env_shift_seed_results.csv",
        10,
    )


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def f(x, default=np.nan):
    try:
        return float(x)
    except Exception:
        return default


def save_fig_data(name: str, payload: dict) -> None:
    p = PF / "figure_data" / f"{name}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def fig_baselines_agency() -> None:
    import matplotlib.pyplot as plt

    a_path, _, _, n_lab = abc_paths()
    rows = load_csv(a_path)
    if not rows:
        return
    by = defaultdict(list)
    for r in rows:
        by[r["condition"]].append(f(r["mean_agency"]))
    conds = ["full", "reactive", "nohippo", "no_homeostasis", "nopfc", "td_direct"]
    conds = [c for c in conds if c in by]
    data = [by[c] for c in conds]
    save_fig_data(
        "fig_baselines_agency",
        {"conditions": conds, "seed_values": {c: by[c] for c in conds}, "n_seeds": n_lab, "source": str(a_path)},
    )
    fig, ax = plt.subplots(figsize=(8, 4.5))
    parts = ax.violinplot(data, showmeans=False, showmedians=True)
    for i, vals in enumerate(data, start=1):
        ax.scatter(np.full(len(vals), i), vals, alpha=0.7, s=28, zorder=3)
    ax.set_xticks(range(1, len(conds) + 1))
    ax.set_xticklabels(conds, rotation=20, ha="right")
    ax.set_ylabel("mean_agency (per seed)")
    ax.set_title(f"Baselines A — agency (compact, n={n_lab}, 100 ticks)")
    fig.tight_layout()
    (PF / "figures").mkdir(parents=True, exist_ok=True)
    fig.savefig(PF / "figures" / "fig_baselines_agency.png", dpi=300)
    plt.close(fig)


def fig_baselines_homeostasis() -> None:
    import matplotlib.pyplot as plt

    a_path, _, _, n_lab = abc_paths()
    rows = load_csv(a_path)
    if not rows:
        return
    by = defaultdict(list)
    for r in rows:
        by[r["condition"]].append(f(r["mean_homeostatic_abs_dev"]))
    conds = ["full", "reactive", "nohippo", "no_homeostasis", "nopfc", "td_direct"]
    conds = [c for c in conds if c in by]
    save_fig_data(
        "fig_baselines_homeostasis",
        {"conditions": conds, "seed_values": {c: by[c] for c in conds}, "n_seeds": n_lab, "source": str(a_path)},
    )
    fig, ax = plt.subplots(figsize=(8, 4.5))
    means = [float(np.mean(by[c])) for c in conds]
    sds = [float(np.std(by[c], ddof=1)) if len(by[c]) > 1 else 0.0 for c in conds]
    x = np.arange(len(conds))
    ax.bar(x, means, yerr=sds, capsize=3, color="#3d5a4c", alpha=0.85)
    for i, c in enumerate(conds):
        ax.scatter(np.full(len(by[c]), i), by[c], color="#1a1a1a", s=22, zorder=3, alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(conds, rotation=20, ha="right")
    ax.set_ylabel("mean homeostatic |dev|")
    ax.set_title(f"Baselines A — homeostatic |dev| (compact, n={n_lab})")
    fig.tight_layout()
    fig.savefig(PF / "figures" / "fig_baselines_homeostasis.png", dpi=300)
    plt.close(fig)


def fig_agency_break() -> None:
    import matplotlib.pyplot as plt

    _, b_path, _, n_lab = abc_paths()
    rows = load_csv(b_path)
    if not rows:
        return
    by = defaultdict(lambda: {"agency": [], "override": []})
    for r in rows:
        by[r["condition"]]["agency"].append(f(r["mean_agency"]))
        by[r["condition"]]["override"].append(f(r["agency_override_rate"]))
    save_fig_data("fig_agency_break", {"n_seeds": n_lab, **{k: v for k, v in by.items()}})
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    conds = [c for c in ("full", "agency_break") if c in by]
    for ax, metric, title in zip(
        axes,
        ("agency", "override"),
        ("mean_agency", "agency_override_rate"),
    ):
        data = [by[c][metric] for c in conds]
        ax.boxplot(data, tick_labels=conds)
        for i, vals in enumerate(data, start=1):
            ax.scatter(np.full(len(vals), i), vals, alpha=0.75, s=28)
        ax.set_title(title)
    fig.suptitle(f"Agency-break B (compact, n={n_lab}) — control vs full")
    fig.tight_layout()
    fig.savefig(PF / "figures" / "fig_agency_break.png", dpi=300)
    plt.close(fig)


def fig_historical_e1() -> None:
    import matplotlib.pyplot as plt

    hist = PF / "raw_results" / "historical"
    metrics = ("mean_agency", "mean_spike_aligned", "remembered_rate")
    by = defaultdict(lambda: defaultdict(list))
    for name in hist.glob("e1_*_summary.csv"):
        cond = name.stem.replace("e1_", "").replace("_summary", "")
        for r in load_csv(name):
            for m in metrics:
                by[cond][m].append(f(r.get(m, 0)))
    if not by:
        return
    conds = sorted(by.keys())
    save_fig_data("fig_historical_e1", {c: dict(by[c]) for c in conds})
    x = np.arange(len(conds))
    width = 0.25
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for i, m in enumerate(metrics):
        means = [float(np.mean(by[c][m])) if by[c][m] else 0 for c in conds]
        errs = [
            float(np.std(by[c][m], ddof=1)) if len(by[c][m]) > 1 else 0 for c in conds
        ]
        ax.bar(x + i * width, means, width, yerr=errs, capsize=3, label=m)
    ax.set_xticks(x + width)
    ax.set_xticklabels(conds)
    ax.set_title("Historical E1 (10k, n=5) — descriptive only")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PF / "figures" / "fig_historical_e1.png", dpi=300)
    plt.close(fig)


def fig_env_shift() -> None:
    import matplotlib.pyplot as plt

    _, _, c_path, n_lab = abc_paths()
    rows = load_csv(c_path)
    if not rows:
        return
    # discrimination drank_success rate by aff
    disc = [r for r in rows if r.get("task") == "discrimination"]
    transfer = [r for r in rows if r.get("task") == "transfer_fountain"]
    payload = {"discrimination": disc, "transfer": transfer, "n_seeds": n_lab, "source": str(c_path)}
    save_fig_data("fig_env_shift", payload)

    def rate(subset, key, truth="True"):
        if not subset:
            return np.nan
        vals = []
        for r in subset:
            v = str(r.get(key, "")).lower()
            vals.append(1.0 if v in ("true", "1", "yes") else 0.0)
        return float(np.mean(vals))

    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for ax, task_rows, title, key in [
        (axes[0], disc, "Discrimination drank_success", "drank_success"),
        (axes[1], transfer, "Transfer phase2_success", "phase2_success"),
    ]:
        off = [r for r in task_rows if str(r.get("affordances")).lower() in ("false", "0")]
        on = [r for r in task_rows if str(r.get("affordances")).lower() in ("true", "1")]
        rates = [rate(off, key), rate(on, key)]
        ax.bar([0, 1], rates, color=["#6b6b6b", "#2f6f4e"])
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["aff_off", "aff_on"])
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("success rate")
        ax.set_title(title)
        # seed points as jittered 0/1
        for i, subset in enumerate((off, on)):
            ys = [
                1.0 if str(r.get(key, "")).lower() in ("true", "1", "yes") else 0.0
                for r in subset
            ]
            ax.scatter(
                np.full(len(ys), i) + np.random.default_rng(0).normal(0, 0.04, len(ys)),
                ys,
                s=22,
                alpha=0.7,
                color="#111",
            )
    fig.suptitle(f"Env shift C (compact Arena, n={n_lab})")
    fig.tight_layout()
    fig.savefig(PF / "figures" / "fig_env_shift.png", dpi=300)
    plt.close(fig)


def fig_architecture_schematic() -> None:
    """SCHEMATIC / DIAGRAM — not empirical."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    boxes = [
        (0.3, 3.2, "World / Body"),
        (2.5, 3.2, "Perception\n+ Drives"),
        (4.7, 3.2, "PFC–Limbic\nDeliberation"),
        (7.0, 3.2, "BG gate /\nMotor"),
        (2.5, 1.0, "Bias-only:\nAffordance / TD /\nGrounding / LLM"),
        (7.0, 1.0, "choice_key\nwriter: PFC only\n(default)"),
    ]
    for x, y, t in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, y), 1.9, 1.4, boxstyle="round,pad=0.05", facecolor="#e8eee9", edgecolor="#222"
            )
        )
        ax.text(x + 0.95, y + 0.7, t, ha="center", va="center", fontsize=8)
    ax.annotate("", xy=(2.5, 3.9), xytext=(2.2, 3.9), arrowprops=dict(arrowstyle="->"))
    ax.annotate("", xy=(4.7, 3.9), xytext=(4.4, 3.9), arrowprops=dict(arrowstyle="->"))
    ax.annotate("", xy=(7.0, 3.9), xytext=(6.6, 3.9), arrowprops=dict(arrowstyle="->"))
    ax.annotate("", xy=(5.6, 3.2), xytext=(4.4, 2.4), arrowprops=dict(arrowstyle="->", ls="--"))
    ax.set_title("SCHEMATIC / DIAGRAM — NEXO agency-preserving loop (not empirical data)")
    fig.tight_layout()
    fig.savefig(PF / "figures" / "fig_architecture_schematic.png", dpi=300)
    plt.close(fig)
    save_fig_data(
        "fig_architecture_schematic",
        {"type": "schematic", "empirical": False, "label": "SCHEMATIC / DIAGRAM"},
    )


def write_tables() -> None:
    tables = PF / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    # Copy master summaries as tables
    for name in ("FINAL_RESULTS_MASTER.csv", "PAIRWISE_COMPARISONS.csv", "SEED_LEVEL_RESULTS.csv"):
        src = PF / name
        if src.exists():
            (tables / name).write_bytes(src.read_bytes())


def main() -> None:
    (PF / "figures").mkdir(parents=True, exist_ok=True)
    fig_baselines_agency()
    fig_baselines_homeostasis()
    fig_agency_break()
    fig_historical_e1()
    fig_env_shift()
    fig_architecture_schematic()
    write_tables()
    print("Figures written to", PF / "figures")


if __name__ == "__main__":
    main()
