#!/usr/bin/env python3
"""
Stats + master CSVs from REAL publication_finalization data only.
No invented p-values; bootstrap when n>=3; mark small-N limits.
"""

from __future__ import annotations

import csv
import json
import math
import os
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PF = ROOT / "publication_finalization"


def git_commit() -> str:
    """Resolve HEAD SHA or fail visibly (never emit NO_GIT_REPOSITORY)."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("cannot resolve git commit: 'git' not on PATH") from exc
    except Exception as exc:
        raise RuntimeError(f"cannot resolve git commit: {exc}") from exc
    commit = (r.stdout or "").strip()
    if r.returncode != 0 or len(commit) != 40:
        detail = (r.stderr or r.stdout or "").strip() or f"exit {r.returncode}"
        raise RuntimeError(f"cannot resolve git commit: {detail}")
    return commit


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fnum(x: Any, default: float = float("nan")) -> float:
    try:
        if x is None or x == "":
            return default
        return float(x)
    except Exception:
        return default


def bootstrap_ci(vals: list[float], n_boot: int = 5000, alpha: float = 0.05) -> tuple[float, float, float]:
    a = np.asarray(vals, dtype=float)
    if len(a) == 0:
        return float("nan"), float("nan"), float("nan")
    mean = float(a.mean())
    if len(a) < 3:
        return mean, float("nan"), float("nan")
    rng = np.random.default_rng(0)
    means = []
    for _ in range(n_boot):
        sample = rng.choice(a, size=len(a), replace=True)
        means.append(float(sample.mean()))
    lo = float(np.quantile(means, alpha / 2))
    hi = float(np.quantile(means, 1 - alpha / 2))
    return mean, lo, hi


def cliffs_delta(a: list[float], b: list[float]) -> float:
    """Cliff's δ effect size (a vs b)."""
    if not a or not b:
        return float("nan")
    gt = lt = 0
    for x in a:
        for y in b:
            if x > y:
                gt += 1
            elif x < y:
                lt += 1
    n = len(a) * len(b)
    return (gt - lt) / n if n else float("nan")


def mannwhitney_u_approx(a: list[float], b: list[float]) -> tuple[float, str]:
    """
    Two-sided Mann–Whitney via normal approx with tie correction.
    Returns (p_approx, note). For n small, mark low confidence.
    """
    x = np.asarray(a, dtype=float)
    y = np.asarray(b, dtype=float)
    if len(x) < 3 or len(y) < 3:
        return float("nan"), "N_TOO_SMALL_for_reliable_test"
    # Rank all
    allv = np.concatenate([x, y])
    order = allv.argsort()
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(allv) + 1, dtype=float)
    # average ties
    _, inv, counts = np.unique(allv, return_inverse=True, return_counts=True)
    for i, c in enumerate(counts):
        if c > 1:
            idx = np.where(inv == i)[0]
            ranks[idx] = ranks[idx].mean()
    r1 = ranks[: len(x)].sum()
    n1, n2 = len(x), len(y)
    u1 = r1 - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    tie = (counts**3 - counts).sum()
    sigma2 = n1 * n2 * (n1 + n2 + 1) / 12 - tie / (12 * (n1 + n2) * (n1 + n2 - 1) + 1e-12)
    sigma = math.sqrt(max(sigma2, 1e-12))
    z = (u1 - mu) / sigma
    # two-sided from normal CDF
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    note = "approx_normal_MW; interpret cautiously at small n"
    if len(x) < 10 or len(y) < 10:
        note += "; n<10"
    return float(p), note


def _primary_abc_roots() -> tuple[Path, Path, Path, str]:
    """Prefer n20_compact campaign; fall back to legacy n=10 paths."""
    n20 = PF / "raw_results" / "n20_compact"
    if (n20 / "baselines_A" / "seed_summaries.csv").exists():
        return (
            n20 / "baselines_A" / "seed_summaries.csv",
            n20 / "agency_break_B" / "seed_summaries.csv",
            n20 / "env_shift_C" / "env_shift_seed_results.csv",
            "n20_compact",
        )
    return (
        PF / "raw_results" / "baselines_A" / "seed_summaries.csv",
        PF / "raw_results" / "agency_break_B" / "seed_summaries.csv",
        PF / "raw_results" / "env_shift_C" / "env_shift_seed_results.csv",
        "legacy_n10",
    )


def collect_seed_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    a_path, b_path, c_path, campaign = _primary_abc_roots()
    mapping = [
        (a_path, "A_baselines"),
        (b_path, "B_agency_break"),
        (PF / "raw_results" / "e1e3_smoke_D" / "seed_summaries.csv", "D_smoke_compact"),
    ]
    # Optional 10k smoke (not primary)
    e10k = PF / "raw_results" / "n20_compact" / "e10k_smoke" / "seed_summaries.csv"
    if not e10k.exists():
        e10k = PF / "raw_results" / "e10k_smoke" / "seed_summaries.csv"
    if e10k.exists():
        mapping.append((e10k, "E_10k_smoke"))

    for path, block in mapping:
        for r in load_csv(path):
            rows.append(
                {
                    "block": block,
                    "campaign": campaign if block.startswith(("A_", "B_")) else "",
                    "condition": r.get("condition", ""),
                    "seed": int(float(r.get("seed", 0))),
                    "profile": r.get("profile", ""),
                    "n_neurons": r.get("n_neurons", ""),
                    "steps": r.get("steps", ""),
                    "mean_agency": fnum(r.get("mean_agency")),
                    "mean_spike_aligned": fnum(r.get("mean_spike_aligned")),
                    "mean_drive_coherent": fnum(r.get("mean_drive_coherent")),
                    "remembered_rate": fnum(r.get("remembered_rate")),
                    "mean_homeostatic_abs_dev": fnum(r.get("mean_homeostatic_abs_dev")),
                    "agency_override_rate": fnum(r.get("agency_override_rate")),
                    "action_entropy_bits": fnum(r.get("action_entropy_bits")),
                    "critical_state_tick_rate": fnum(r.get("critical_state_tick_rate")),
                    "critical_state_tick_count": fnum(r.get("critical_state_tick_count")),
                    "survival_time": r.get("survival_time", "MISSING_not_formalized"),
                    "git_commit": r.get("git_commit", git_commit()),
                    "timestamp_utc": r.get("timestamp_utc", ""),
                    "source_file": str(path.relative_to(ROOT)),
                }
            )
    # stash C path for env-shift loop below via closure attribute
    collect_seed_rows._c_path = c_path  # type: ignore[attr-defined]
    collect_seed_rows._campaign = campaign  # type: ignore[attr-defined]

    # Historical E1
    hist = PF / "raw_results" / "historical"
    for csv_name, cond in [
        ("e1_full_summary.csv", "full"),
        ("e1_nopfc_summary.csv", "nopfc"),
        ("e1_nobind_summary.csv", "nobind"),
        ("e1_nohippo_summary.csv", "nohippo"),
        ("e1_noaffect_summary.csv", "noaffect"),
    ]:
        for r in load_csv(hist / csv_name):
            rows.append(
                {
                    "block": "D_historical_E1_10k",
                    "condition": r.get("condition", cond),
                    "seed": int(float(r.get("seed", 0))),
                    "profile": r.get("profile", "neuro-10k"),
                    "n_neurons": r.get("n_neurons", "10290"),
                    "steps": r.get("steps", "200"),
                    "mean_agency": fnum(r.get("mean_agency")),
                    "mean_spike_aligned": fnum(r.get("mean_spike_aligned")),
                    "mean_drive_coherent": fnum(r.get("mean_drive_coherent")),
                    "remembered_rate": fnum(r.get("remembered_rate")),
                    "mean_homeostatic_abs_dev": float("nan"),
                    "agency_override_rate": 0.0,
                    "git_commit": "HISTORICAL_NO_COMMIT_IN_CSV",
                    "timestamp_utc": "HISTORICAL",
                    "source_file": f"publication_finalization/raw_results/historical/{csv_name}",
                }
            )

    # E2
    for r in load_csv(hist / "e2_llm_invariance.csv"):
        rows.append(
            {
                "block": "D_historical_E2_10k",
                "condition": "llm_invariance",
                "seed": int(float(r.get("seed", 0))),
                "profile": "neuro-10k",
                "n_neurons": "10290",
                "steps": r.get("steps", "100"),
                "mean_agency": float("nan"),
                "mean_spike_aligned": float("nan"),
                "mean_drive_coherent": float("nan"),
                "remembered_rate": float("nan"),
                "mean_homeostatic_abs_dev": float("nan"),
                "agency_override_rate": float("nan"),
                "trajectories_identical": r.get("trajectories_identical"),
                "git_commit": "HISTORICAL_NO_COMMIT_IN_CSV",
                "timestamp_utc": "HISTORICAL",
                "source_file": "publication_finalization/raw_results/historical/e2_llm_invariance.csv",
            }
        )

    # E3
    for r in load_csv(hist / "e3_sleep_recall.csv"):
        rows.append(
            {
                "block": "D_historical_E3_10k",
                "condition": r.get("condition", ""),
                "seed": int(float(r.get("seed", 0))),
                "profile": "neuro-10k",
                "n_neurons": "10290",
                "steps": "",
                "mean_agency": float("nan"),
                "mean_spike_aligned": float("nan"),
                "mean_drive_coherent": float("nan"),
                "remembered_rate": float("nan"),
                "mean_homeostatic_abs_dev": float("nan"),
                "agency_override_rate": float("nan"),
                "mean_recall": fnum(r.get("mean_recall")),
                "git_commit": "HISTORICAL_NO_COMMIT_IN_CSV",
                "timestamp_utc": "HISTORICAL",
                "source_file": "publication_finalization/raw_results/historical/e3_sleep_recall.csv",
            }
        )

    # Env shift (prefer n20_compact)
    c_path = getattr(collect_seed_rows, "_c_path", PF / "raw_results" / "env_shift_C" / "env_shift_seed_results.csv")
    campaign = getattr(collect_seed_rows, "_campaign", "")
    for r in load_csv(c_path):
        rows.append(
            {
                "block": "C_env_shift",
                "campaign": campaign,
                "condition": f"{r.get('task')}:{r.get('condition')}",
                "seed": int(float(r.get("seed", 0))),
                "profile": r.get("profile", "compact"),
                "n_neurons": "",
                "steps": "",
                "mean_agency": float("nan"),
                "mean_spike_aligned": float("nan"),
                "mean_drive_coherent": float("nan"),
                "remembered_rate": float("nan"),
                "mean_homeostatic_abs_dev": float("nan"),
                "agency_override_rate": float("nan"),
                "drank_success": r.get("drank_success", ""),
                "phase2_success": r.get("phase2_success", ""),
                "ticks": r.get("ticks", r.get("phase2_ticks", "")),
                "git_commit": r.get("git_commit", git_commit()),
                "timestamp_utc": r.get("timestamp_utc", ""),
                "source_file": str(Path(c_path).relative_to(ROOT)).replace("\\", "/"),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            out = {}
            for k in keys:
                v = r.get(k, "")
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    out[k] = ""
                else:
                    out[k] = v
            w.writerow(out)


def main() -> None:
    seed_rows = collect_seed_rows()
    campaign = getattr(collect_seed_rows, "_campaign", "unknown")
    write_csv(PF / "SEED_LEVEL_RESULTS.csv", seed_rows)
    if campaign == "n20_compact":
        write_csv(PF / "SEED_LEVEL_RESULTS_n20.csv", seed_rows)
        write_csv(PF / "tables" / "SEED_LEVEL_RESULTS_n20.csv", seed_rows)

    # Master: aggregate by block×condition for numeric metrics
    metrics = [
        "mean_agency",
        "mean_spike_aligned",
        "mean_drive_coherent",
        "remembered_rate",
        "mean_homeostatic_abs_dev",
        "agency_override_rate",
        "action_entropy_bits",
        "critical_state_tick_rate",
        "mean_recall",
    ]
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in seed_rows:
        groups[(r["block"], r["condition"])].append(r)

    master: list[dict[str, Any]] = []
    for (block, cond), items in sorted(groups.items()):
        row: dict[str, Any] = {
            "block": block,
            "condition": cond,
            "n_seeds": len(items),
            "profile": items[0].get("profile", ""),
            "git_commit": git_commit(),
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        for m in metrics:
            vals = [fnum(it.get(m)) for it in items if not math.isnan(fnum(it.get(m)))]
            if not vals:
                row[f"{m}_mean"] = ""
                row[f"{m}_sd"] = ""
                row[f"{m}_ci95_lo"] = ""
                row[f"{m}_ci95_hi"] = ""
                continue
            mean, lo, hi = bootstrap_ci(vals)
            sd = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
            row[f"{m}_mean"] = mean
            row[f"{m}_sd"] = sd
            row[f"{m}_ci95_lo"] = "" if math.isnan(lo) else lo
            row[f"{m}_ci95_hi"] = "" if math.isnan(hi) else hi
            if len(vals) < 3:
                row[f"{m}_note"] = "n<3_no_bootstrap_CI"
        master.append(row)
    write_csv(PF / "FINAL_RESULTS_MASTER.csv", master)
    if campaign == "n20_compact":
        write_csv(PF / "FINAL_RESULTS_MASTER_n20.csv", master)
        write_csv(PF / "tables" / "FINAL_RESULTS_MASTER_n20.csv", master)

    # Pairwise within blocks for primary metrics
    pairwise: list[dict[str, Any]] = []
    primary = {
        "A_baselines": ("full", ["reactive", "nohippo", "no_homeostasis", "nopfc", "td_direct"], "mean_agency"),
        "B_agency_break": ("full", ["agency_break"], "mean_agency"),
        "D_historical_E1_10k": ("full", ["nopfc", "nobind", "nohippo", "noaffect"], "mean_agency"),
        "D_historical_E3_10k": ("control", ["sleep"], "mean_recall"),
    }
    for block, (ref, others, metric) in primary.items():
        ref_vals = [
            fnum(r.get(metric))
            for r in seed_rows
            if r["block"] == block and r["condition"] == ref and not math.isnan(fnum(r.get(metric)))
        ]
        for oth in others:
            oth_metric = metric
            if block == "D_historical_E1_10k" and oth == "nobind":
                oth_metric = "mean_spike_aligned"
                # compare spike_aligned full vs nobind
                ref_vals_m = [
                    fnum(r.get("mean_spike_aligned"))
                    for r in seed_rows
                    if r["block"] == block and r["condition"] == ref and not math.isnan(fnum(r.get("mean_spike_aligned")))
                ]
                oth_vals = [
                    fnum(r.get(oth_metric))
                    for r in seed_rows
                    if r["block"] == block and r["condition"] == oth and not math.isnan(fnum(r.get(oth_metric)))
                ]
                p, note = mannwhitney_u_approx(ref_vals_m, oth_vals)
                pairwise.append(
                    {
                        "block": block,
                        "metric": oth_metric,
                        "condition_a": ref,
                        "condition_b": oth,
                        "n_a": len(ref_vals_m),
                        "n_b": len(oth_vals),
                        "mean_a": float(np.mean(ref_vals_m)) if ref_vals_m else "",
                        "mean_b": float(np.mean(oth_vals)) if oth_vals else "",
                        "cliffs_delta_a_minus_b": cliffs_delta(ref_vals_m, oth_vals),
                        "p_mannwhitney_approx": "" if math.isnan(p) else p,
                        "note": note,
                    }
                )
                continue
            if block == "D_historical_E1_10k" and oth == "nohippo":
                oth_metric = "remembered_rate"
                ref_vals_m = [
                    fnum(r.get("remembered_rate"))
                    for r in seed_rows
                    if r["block"] == block and r["condition"] == ref and not math.isnan(fnum(r.get("remembered_rate")))
                ]
                oth_vals = [
                    fnum(r.get(oth_metric))
                    for r in seed_rows
                    if r["block"] == block and r["condition"] == oth and not math.isnan(fnum(r.get(oth_metric)))
                ]
                p, note = mannwhitney_u_approx(ref_vals_m, oth_vals)
                pairwise.append(
                    {
                        "block": block,
                        "metric": oth_metric,
                        "condition_a": ref,
                        "condition_b": oth,
                        "n_a": len(ref_vals_m),
                        "n_b": len(oth_vals),
                        "mean_a": float(np.mean(ref_vals_m)) if ref_vals_m else "",
                        "mean_b": float(np.mean(oth_vals)) if oth_vals else "",
                        "cliffs_delta_a_minus_b": cliffs_delta(ref_vals_m, oth_vals),
                        "p_mannwhitney_approx": "" if math.isnan(p) else p,
                        "note": note,
                    }
                )
                continue

            oth_vals = [
                fnum(r.get(oth_metric if oth_metric != metric else metric))
                for r in seed_rows
                if r["block"] == block
                and r["condition"] == oth
                and not math.isnan(fnum(r.get(metric if oth not in ("nobind", "nohippo") else oth_metric)))
            ]
            # simplify: always use metric for non-special
            oth_vals = [
                fnum(r.get(metric))
                for r in seed_rows
                if r["block"] == block and r["condition"] == oth and not math.isnan(fnum(r.get(metric)))
            ]
            p, note = mannwhitney_u_approx(ref_vals, oth_vals)
            pairwise.append(
                {
                    "block": block,
                    "metric": metric,
                    "condition_a": ref,
                    "condition_b": oth,
                    "n_a": len(ref_vals),
                    "n_b": len(oth_vals),
                    "mean_a": float(np.mean(ref_vals)) if ref_vals else "",
                    "mean_b": float(np.mean(oth_vals)) if oth_vals else "",
                    "cliffs_delta_a_minus_b": cliffs_delta(ref_vals, oth_vals),
                    "p_mannwhitney_approx": "" if math.isnan(p) else p,
                    "note": note
                    + (
                        "; zero_variance_possible"
                        if (len(set(ref_vals)) <= 1 and len(set(oth_vals)) <= 1)
                        else ""
                    ),
                }
            )

    # Also pairwise mean_homeostatic_abs_dev for baselines
    ref_h = [
        fnum(r.get("mean_homeostatic_abs_dev"))
        for r in seed_rows
        if r["block"] == "A_baselines"
        and r["condition"] == "full"
        and not math.isnan(fnum(r.get("mean_homeostatic_abs_dev")))
    ]
    for oth in ["reactive", "nohippo", "no_homeostasis", "nopfc", "td_direct"]:
        oth_h = [
            fnum(r.get("mean_homeostatic_abs_dev"))
            for r in seed_rows
            if r["block"] == "A_baselines"
            and r["condition"] == oth
            and not math.isnan(fnum(r.get("mean_homeostatic_abs_dev")))
        ]
        p, note = mannwhitney_u_approx(ref_h, oth_h)
        pairwise.append(
            {
                "block": "A_baselines",
                "metric": "mean_homeostatic_abs_dev",
                "condition_a": "full",
                "condition_b": oth,
                "n_a": len(ref_h),
                "n_b": len(oth_h),
                "mean_a": float(np.mean(ref_h)) if ref_h else "",
                "mean_b": float(np.mean(oth_h)) if oth_h else "",
                "cliffs_delta_a_minus_b": cliffs_delta(ref_h, oth_h),
                "p_mannwhitney_approx": "" if math.isnan(p) else p,
                "note": note,
            }
        )

    write_csv(PF / "PAIRWISE_COMPARISONS.csv", pairwise)
    if campaign == "n20_compact":
        write_csv(PF / "PAIRWISE_COMPARISONS_n20.csv", pairwise)
        write_csv(PF / "tables" / "PAIRWISE_COMPARISONS_n20.csv", pairwise)

    # STATISTICAL_REPORT.md
    a_n = len([r for r in seed_rows if r["block"] == "A_baselines" and r["condition"] == "full"])
    lines = [
        "# STATISTICAL_REPORT",
        "",
        f"- Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- git_commit: `{git_commit()}`",
        f"- Primary A/B/C campaign: `{campaign}`",
        f"- Seed-level rows: {len(seed_rows)}",
        f"- Master groups: {len(master)}",
        f"- Pairwise rows: {len(pairwise)}",
        f"- Compact A full-condition seeds: {a_n}",
        "",
        "## Policy",
        "",
        "- Only real CSVs under `publication_finalization/raw_results/` (+ copied historical).",
        "- Bootstrap 95% CI for means when **n≥3** (5000 resamples, seed 0).",
        "- Mann–Whitney normal approximation when n≥3 per arm.",
        f"- Compact A/B/C primary: **n={a_n}** seeds × 100 ticks (see `EVIDENCE_GAP_FILL.md`). Historical E1–E3 remain **n=5 @10k**.",
        "- Zero across-seed variance (common in E1 full) makes inferential tests degenerate — report descriptives explicitly.",
        "- Do **not** mix compact A/B/C with historical 10k E1–E3 in one unlabeled inference.",
        "- `action_entropy_bits` / `critical_state_tick_*` are study-derived from tick logs; `survival_time` remains **MISSING**.",
        "",
        "## Blocks present",
        "",
    ]
    blocks = sorted({r["block"] for r in seed_rows})
    for b in blocks:
        n = sum(1 for r in seed_rows if r["block"] == b)
        lines.append(f"- `{b}`: {n} seed-level rows")
    lines += [
        "",
        "## Files",
        "",
        "- `SEED_LEVEL_RESULTS.csv` (+ `*_n20.csv` when campaign is n20_compact)",
        "- `FINAL_RESULTS_MASTER.csv`",
        "- `PAIRWISE_COMPARISONS.csv`",
        "",
        "## Deferred / missing",
        "",
        "- Full 10k × 20-seed replication of E1–E3: **NOT RUN / deferred**",
        "- Formal survival_time (episode until death/termination): **MISSING** (not formalized in core)",
        "- External public benchmark: **MISSING**",
        "- Multiple-comparison Holm across all DVs: not applied globally (exploratory pairwise only)",
        "",
    ]
    (PF / "STATISTICAL_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("Wrote SEED_LEVEL_RESULTS / MASTER / PAIRWISE / STATISTICAL_REPORT", f"campaign={campaign}")


if __name__ == "__main__":
    main()
