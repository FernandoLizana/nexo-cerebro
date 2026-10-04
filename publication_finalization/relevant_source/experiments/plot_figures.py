"""
Genera figuras del paper desde CSV/JSONL en experiments/results/.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def _load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _mean_std(vals: list[float]) -> tuple[float, float]:
    if not vals:
        return 0.0, 0.0
    a = np.asarray(vals, dtype=float)
    return float(a.mean()), float(a.std(ddof=1) if len(a) > 1 else 0.0)


def plot_ablation(results_dir: Path, fig_dir: Path) -> None:
    import matplotlib.pyplot as plt

    metrics = ("mean_agency", "mean_spike_aligned", "mean_drive_coherent", "inhibited_rate")
    labels = {
        "mean_agency": "Agency",
        "mean_spike_aligned": "Spike alignment",
        "mean_drive_coherent": "Drive coherence",
        "inhibited_rate": "PFC inhibition rate",
    }
    by_cond: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for csv_path in sorted(results_dir.glob("e1_*_summary.csv")):
        cond = csv_path.stem.replace("e1_", "").replace("_summary", "")
        for row in _load_csv(csv_path):
            for m in metrics:
                by_cond[cond][m].append(float(row.get(m, 0)))

    if not by_cond:
        return

    conds = sorted(by_cond.keys())
    x = np.arange(len(conds))
    width = 0.2
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for i, m in enumerate(metrics):
        means = [_mean_std(by_cond[c][m])[0] for c in conds]
        errs = [_mean_std(by_cond[c][m])[1] for c in conds]
        ax.bar(x + i * width, means, width, yerr=errs, capsize=3, label=labels[m])
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(conds)
    ax.set_ylabel("Mean ± SD")
    ax.set_title("E1 — Ablation of intention circuit components")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig1_ablation.png", dpi=150)
    plt.close(fig)


def plot_spike_alignment(results_dir: Path, fig_dir: Path) -> None:
    import matplotlib.pyplot as plt

    series: dict[str, list[float]] = defaultdict(list)
    for jsonl in sorted(results_dir.glob("e1_full_s*.jsonl")):
        ticks: list[float] = []
        with jsonl.open(encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                ticks.append(float(row.get("spike_aligned", 0)))
        if ticks:
            series["full"].append(float(np.mean(ticks)))

    for jsonl in sorted(results_dir.glob("e1_nobind_s*.jsonl")):
        ticks = []
        with jsonl.open(encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                ticks.append(float(row.get("spike_aligned", 0)))
        if ticks:
            series["nobind"].append(float(np.mean(ticks)))

    if not series:
        return

    fig, ax = plt.subplots(figsize=(5, 4))
    labels = list(series.keys())
    data = [series[k] for k in labels]
    ax.boxplot(data, tick_labels=labels)
    ax.set_ylabel("Mean spike alignment per run")
    ax.set_title("E1 — Spike alignment: Full vs NoBind")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig2_spike_alignment.png", dpi=150)
    plt.close(fig)


def plot_llm_invariance(results_dir: Path, fig_dir: Path) -> None:
    import matplotlib.pyplot as plt

    rows = _load_csv(results_dir / "e2_llm_invariance.csv")
    if not rows:
        return

    identical = sum(1 for r in rows if r.get("trajectories_identical", "").lower() in ("true", "1"))
    n = len(rows)
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.bar(["Identical", "Differ"], [identical, n - identical], color=["#2a9d8f", "#e76f51"])
    ax.set_ylabel("Seeds")
    ax.set_title(f"E2 — Motor/deliberation invariance (LLM on/off)\n{identical}/{n} seeds identical")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig3_llm_invariance.png", dpi=150)
    plt.close(fig)


def plot_sleep_recall(results_dir: Path, fig_dir: Path) -> None:
    import matplotlib.pyplot as plt

    rows = _load_csv(results_dir / "e3_sleep_recall.csv")
    if not rows:
        return

    by_cond: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        by_cond[r["condition"]].append(float(r["mean_recall"]))

    labels = sorted(by_cond.keys())
    means = [_mean_std(by_cond[k])[0] for k in labels]
    errs = [_mean_std(by_cond[k])[1] for k in labels]

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(labels, means, yerr=errs, capsize=4, color=["#457b9d", "#f4a261"])
    ax.set_ylabel("Mean recall score")
    ax.set_ylim(0, 1.05)
    ax.set_title("E3 — Recall after sleep vs control")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig4_sleep_recall.png", dpi=150)
    plt.close(fig)


def plot_e4_selective_sleep(results_dir: Path, fig_dir: Path) -> None:
    import matplotlib.pyplot as plt

    rows = _load_csv(results_dir / "e4_sleep_selective.csv")
    if not rows:
        return

    by: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        c = r["condition"]
        by[c]["emotional"].append(float(r["mean_recall_emotional"]))
        by[c]["neutral"].append(float(r["mean_recall_neutral"]))

    conds = [c for c in ("control", "uniform", "selective") if c in by]
    if not conds:
        conds = sorted(by.keys())
    x = np.arange(len(conds))
    width = 0.35
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    emo_m = [_mean_std(by[c]["emotional"])[0] for c in conds]
    emo_e = [_mean_std(by[c]["emotional"])[1] for c in conds]
    neu_m = [_mean_std(by[c]["neutral"])[0] for c in conds]
    neu_e = [_mean_std(by[c]["neutral"])[1] for c in conds]
    ax.bar(x - width / 2, emo_m, width, yerr=emo_e, capsize=3, label="Emotional", color="#264653")
    ax.bar(x + width / 2, neu_m, width, yerr=neu_e, capsize=3, label="Neutral", color="#2a9d8f")
    ax.set_xticks(x)
    ax.set_xticklabels(conds)
    ax.set_ylabel("Mean recall ± SD")
    ax.set_ylim(0, 1.08)
    ax.set_title("E4 — Selective vs uniform sleep recall")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig5_e4_selective_sleep.png", dpi=150)
    plt.close(fig)


def plot_e5_grounding(results_dir: Path, fig_dir: Path) -> None:
    import matplotlib.pyplot as plt

    rows = _load_csv(results_dir / "e5_grounding.csv")
    if not rows:
        return

    by: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        by[r["condition"]].append(float(r.get("seek_food_after_speak", 0)))

    labels = [c for c in ("ground_off", "ground_on") if c in by] or sorted(by.keys())
    means = [_mean_std(by[k])[0] for k in labels]
    errs = [_mean_std(by[k])[1] for k in labels]

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(labels, means, yerr=errs, capsize=4, color=["#6c757d", "#e9c46a"])
    ax.set_ylabel("seek_food after caregiver utterance")
    ax.set_title("E5 — Language grounding drive bias\n(never sets choice_key)")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig6_e5_grounding.png", dpi=150)
    plt.close(fig)


def plot_e7_multimodal(results_dir: Path, fig_dir: Path) -> None:
    import matplotlib.pyplot as plt

    rows = _load_csv(results_dir / "e7_multimodal.csv")
    if not rows:
        return

    by: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        by[r["condition"]].append(float(r.get("thalamic_world_gain", 0)))

    labels = [c for c in ("full_sense", "no_vision") if c in by] or sorted(by.keys())
    means = [_mean_std(by[k])[0] for k in labels]
    errs = [_mean_std(by[k])[1] for k in labels]

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(labels, means, yerr=errs, capsize=4, color=["#457b9d", "#e76f51"])
    ax.set_ylabel("Thalamic world gain")
    ax.set_title("E7 — Vision ablation (multimodal hub)")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig7_e7_multimodal.png", dpi=150)
    plt.close(fig)


def plot_bench_tick(results_dir: Path, fig_dir: Path) -> None:
    import matplotlib.pyplot as plt

    rows = _load_csv(results_dir / "bench_tick_gpu.csv")
    ok = [r for r in rows if str(r.get("ok", "")).lower() in ("true", "1")]
    if not ok:
        return
    labels = [r["profile"] for r in ok]
    ms = [float(r["ms_per_tick"]) for r in ok]
    lif = [int(float(r["active_lif"])) for r in ok]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(labels, ms, color="#1d3557")
    ax.set_ylabel("ms / tick")
    ax.set_title("Tick latency by active LIF profile")
    for i, (m, n) in enumerate(zip(ms, lif)):
        ax.text(i, m, f"  {n} LIF", va="bottom", fontsize=8)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig8_bench_tick.png", dpi=150)
    plt.close(fig)


def plot_e8_causal_arena(results_dir: Path, fig_dir: Path) -> None:
    """Level 2 causal Arena — discriminación aff_on vs aff_off (compact)."""
    import matplotlib.pyplot as plt

    path = results_dir / "arena_discrimination.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("rows") or []
    if not rows:
        return

    by: dict[str, list[float]] = defaultdict(list)
    success: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        cond = "aff_on" if r.get("affordances") else "aff_off"
        by[cond].append(float(r.get("ticks", 0)))
        success[cond].append(1.0 if r.get("drank_success") else 0.0)

    labels = [c for c in ("aff_off", "aff_on") if c in by]
    if not labels:
        return
    tick_m = [_mean_std(by[k])[0] for k in labels]
    tick_e = [_mean_std(by[k])[1] for k in labels]
    succ_m = [_mean_std(success[k])[0] for k in labels]

    fig, axes = plt.subplots(1, 2, figsize=(8, 3.6))
    colors = ["#adb5bd", "#2a9d8f"]
    axes[0].bar(labels, tick_m, yerr=tick_e, capsize=4, color=colors[: len(labels)])
    axes[0].set_ylabel("Ticks to drink (mean ± SD)")
    axes[0].set_title("E8 — Discrimination latency")
    axes[1].bar(labels, succ_m, color=colors[: len(labels)])
    axes[1].set_ylim(0, 1.15)
    axes[1].set_ylabel("Success rate")
    axes[1].set_title("E8 — Drink success (good fountain)")
    fig.suptitle(
        "Level 2 causal Arena: good vs dry fountain (compact)",
        fontsize=11,
    )
    fig.tight_layout()
    fig.savefig(fig_dir / "fig9_e8_causal_arena.png", dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="indir", default="experiments/results")
    parser.add_argument("--fig", default="experiments/figures")
    args = parser.parse_args()

    results_dir = Path(args.indir)
    fig_dir = Path(args.fig)
    fig_dir.mkdir(parents=True, exist_ok=True)

    plot_ablation(results_dir, fig_dir)
    plot_spike_alignment(results_dir, fig_dir)
    plot_llm_invariance(results_dir, fig_dir)
    plot_sleep_recall(results_dir, fig_dir)
    plot_e4_selective_sleep(results_dir, fig_dir)
    plot_e5_grounding(results_dir, fig_dir)
    plot_e7_multimodal(results_dir, fig_dir)
    plot_bench_tick(results_dir, fig_dir)
    plot_e8_causal_arena(results_dir, fig_dir)
    print(f"Figuras -> {fig_dir.resolve()}")
    for p in sorted(fig_dir.glob("fig*.png")):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
