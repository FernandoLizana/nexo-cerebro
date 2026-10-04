#!/usr/bin/env python3
"""
Publication finalization runners — study-only wrappers (AblationFlags + patches).

Does NOT modify NEXO core behavior defaults. Overrides are EXPERIMENTAL CONTROLS
for Adaptive Behavior baselines / agency-break contrasts only.
Outputs go under publication_finalization/ only (never overwrite experiments/results/).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shutil
import tempfile
import time
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(ROOT))

from brain.deliberation import ACTION_SCHEMAS, DeliberationResult
from brain.experiment_flags import AblationFlags, apply_condition
from brain.mind import InfantApeBrain
from brain.profile import profile_neuron_count
from experiments.gpu_env import enable_experiment_gpu, release_experiment_gpu
from experiments.metrics import extract_tick_metrics, write_summary_csv
from experiments.profile_select import resolve_experiment_profile, set_profile_env

PF = ROOT / "publication_finalization"
DRIVE_TO_SCHEMA = {s["drive"]: s for s in ACTION_SCHEMAS if s.get("drive")}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_commit() -> str:
    """Resolve HEAD SHA or fail visibly (never emit NO_GIT_REPOSITORY)."""
    import subprocess

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


def _schema_for_drive(drive: str) -> tuple[str, str, str]:
    s = DRIVE_TO_SCHEMA.get(drive)
    if not s:
        return "wander", "deambular", ""
    return s["key"], s["label"], s["drive"]


def _homeostatic_abs_dev(body: Any) -> float:
    """Sum of |state - mid setpoint| for core vars; study metric, not biological claim."""
    # Body vars: hunger/thirst/fatigue rise with need; hygiene/bladder rise with unmet need.
    pairs = (
        ("hunger", 0.28),
        ("thirst", 0.22),
        ("fatigue", 0.20),
        ("hygiene", 0.18),
        ("comfort", 0.62),
    )
    total = 0.0
    for name, sp in pairs:
        total += abs(float(getattr(body, name, sp)) - sp)
    return float(total)


# Study thresholds for critical-state tick counts (NOT survival_time; documented in EVIDENCE_GAP_FILL).
_CRITICAL_HUNGER = 0.85
_CRITICAL_THIRST = 0.85
_CRITICAL_FATIGUE = 0.90


def _is_critical_state(body: Any) -> bool:
    """True if any core need exceeds study-defined critical threshold."""
    return (
        float(getattr(body, "hunger", 0.0)) >= _CRITICAL_HUNGER
        or float(getattr(body, "thirst", 0.0)) >= _CRITICAL_THIRST
        or float(getattr(body, "fatigue", 0.0)) >= _CRITICAL_FATIGUE
    )


def _action_entropy(choice_keys: list[str]) -> float:
    """Shannon entropy (bits) of choice_key distribution over ticks; 0 if empty/single."""
    if not choice_keys:
        return 0.0
    counts: dict[str, int] = {}
    for k in choice_keys:
        key = k or "_empty_"
        counts[key] = counts.get(key, 0) + 1
    n = len(choice_keys)
    h = 0.0
    for c in counts.values():
        p = c / n
        if p > 0:
            h -= p * math.log2(p)
    return float(h)


def _make_brain(seed: int, flags: AblationFlags, state_root: Path) -> InfantApeBrain:
    np.random.seed(seed)
    p = resolve_experiment_profile()
    brain = InfantApeBrain(
        profile=p,
        state_dir=state_root,
        headless=True,
        auto_save=False,
        experiment_flags=flags,
    )
    brain.world._rng = np.random.default_rng(seed)  # noqa: SLF001
    return brain


def _patch_reactive(brain: InfantApeBrain) -> None:
    """Baseline: after deliberation, force schema of argmax drive (rule-reactive)."""
    original = brain.deliberation.run

    def run(br: InfantApeBrain, *a: Any, **kw: Any) -> DeliberationResult:
        result = original(br, *a, **kw)
        drives = br._merged_drives()
        if drives:
            top = max(drives.items(), key=lambda x: x[1])[0]
            key, label, dk = _schema_for_drive(top)
            result.choice_key = key
            result.choice = label
            result.drive_key = dk
            result.agency = 0.0
            result.inhibited = False
            br.deliberation.last = result
            br._pub_agency_override = "reactive_drive_argmax"  # noqa: SLF001
        return result

    brain.deliberation.run = run  # type: ignore[method-assign]


def _patch_no_homeostasis(brain: InfantApeBrain) -> None:
    """Approximate no-homeostasis: freeze body tick + flat drives (study wrapper)."""
    body = brain.body
    snap = {
        "hunger": float(body.hunger),
        "thirst": float(body.thirst),
        "fatigue": float(body.fatigue),
        "comfort": float(body.comfort),
        "hygiene": float(getattr(body, "hygiene", 0.7)),
        "bladder": float(getattr(body, "bladder", 0.2)),
        "pain": float(getattr(body, "pain", 0.0)) if hasattr(body, "pain") else 0.0,
    }
    orig_tick = body.tick

    def frozen_tick(*a: Any, **kw: Any) -> Any:
        out = orig_tick(*a, **kw)
        for k, v in snap.items():
            if hasattr(body, k):
                setattr(body, k, v)
        return out

    body.tick = frozen_tick  # type: ignore[method-assign]

    def flat_drives() -> dict[str, float]:
        return {k: 0.0 for k in ("seek_food", "seek_water", "seek_rest", "sleep_need", "seek_hygiene")}

    brain._merged_drives = flat_drives  # type: ignore[method-assign]
    brain._pub_agency_override = "no_homeostasis_freeze"  # noqa: SLF001


def _patch_td_direct(brain: InfantApeBrain) -> None:
    """
    Control: TD table selects choice_key (agency-break learner-direct).
    NOT a product improvement — experimental contrast only.
    """
    original = brain.deliberation.run

    def run(br: InfantApeBrain, *a: Any, **kw: Any) -> DeliberationResult:
        result = original(br, *a, **kw)
        td = getattr(br, "td_reward", None)
        drives = br._merged_drives()
        top = max(drives.items(), key=lambda x: x[1])[0] if drives else ""
        room = br.world.current_room() if hasattr(br.world, "current_room") else ""
        hour = 12
        keys = [s["key"] for s in ACTION_SCHEMAS]
        best_key = result.choice_key
        best_v = -1e9
        if td is not None:
            for k in keys:
                v = float(td.predicted_value(room, top, k, hour=hour))
                if v > best_v:
                    best_v = v
                    best_key = k
        # If TD table empty, fall back to drive-argmax (still non-PFC commit)
        if best_v <= -1e8 + 1:
            if top:
                best_key, label, dk = _schema_for_drive(top)
            else:
                best_key, label, dk = "wander", "deambular", ""
        else:
            sch = next((s for s in ACTION_SCHEMAS if s["key"] == best_key), None)
            label = sch["label"] if sch else best_key
            dk = sch["drive"] if sch else ""
        result.choice_key = best_key
        result.choice = label
        result.drive_key = dk
        result.agency = 0.0
        br.deliberation.last = result
        br._pub_agency_override = "td_direct_choice"  # noqa: SLF001
        return result

    brain.deliberation.run = run  # type: ignore[method-assign]


def _patch_agency_break_force_drive(brain: InfantApeBrain) -> None:
    """Agency-break control: force drink/eat from top physiological need, bypass net contest."""
    original = brain.deliberation.run

    def run(br: InfantApeBrain, *a: Any, **kw: Any) -> DeliberationResult:
        result = original(br, *a, **kw)
        # Force outside deliberation winner: map body extremes → schema
        hunger = float(br.body.hunger)
        thirst = float(br.body.thirst)
        if thirst >= hunger and thirst > 0.45:
            key, label, dk = "drink", "beber", "seek_water"
        elif hunger > 0.45:
            key, label, dk = "eat", "comer", "seek_food"
        else:
            key, label, dk = "wander", "deambular", ""
        result.choice_key = key
        result.choice = label
        result.drive_key = dk
        result.agency = 0.0
        result.inhibited = False
        br.deliberation.last = result
        br._pub_agency_override = "force_body_schema"  # noqa: SLF001
        return result

    brain.deliberation.run = run  # type: ignore[method-assign]


CONDITION_BUILDERS: dict[str, Callable[[], tuple[AblationFlags, Callable[[InfantApeBrain], None] | None]]] = {
    "full": lambda: (apply_condition("full"), None),
    "nohippo": lambda: (apply_condition("nohippo"), None),
    "nopfc": lambda: (apply_condition("nopfc"), None),
    "reactive": lambda: (apply_condition("full"), _patch_reactive),
    "no_homeostasis": lambda: (apply_condition("full"), _patch_no_homeostasis),
    "td_direct": lambda: (
        replace(apply_condition("full"), enable_td_reward=True),
        _patch_td_direct,
    ),
    "agency_break": lambda: (apply_condition("full"), _patch_agency_break_force_drive),
}


def run_condition_episode(
    *,
    condition: str,
    seed: int,
    steps: int,
    jsonl_path: Path | None,
) -> dict[str, Any]:
    flags, patch = CONDITION_BUILDERS[condition]()
    sd = Path(tempfile.mkdtemp(prefix=f"pub_{condition}_{seed}_"))
    brain = _make_brain(seed, flags, sd)
    if patch:
        patch(brain)

    rows: list[dict[str, Any]] = []
    agency_overrides = 0
    if jsonl_path and jsonl_path.exists():
        jsonl_path.unlink()
    if jsonl_path:
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        for t in range(steps):
            out = brain.world_tick(steps=1)
            tm = extract_tick_metrics(out, tick=t, seed=seed, condition=condition)
            override = getattr(brain, "_pub_agency_override", "") or ""
            if override:
                agency_overrides += 1
            body = brain.body
            row = tm.to_dict()
            row.update(
                {
                    "hunger": float(body.hunger),
                    "thirst": float(body.thirst),
                    "fatigue": float(body.fatigue),
                    "homeostatic_abs_dev": _homeostatic_abs_dev(body),
                    "agency_override": override,
                    "profile": brain.profile.name,
                    "n_neurons": profile_neuron_count(brain.profile),
                }
            )
            rows.append(row)
            if jsonl_path:
                with jsonl_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
            if hasattr(brain, "_pub_agency_override"):
                delattr(brain, "_pub_agency_override")
    finally:
        shutil.rmtree(sd, ignore_errors=True)

    n = len(rows) or 1
    critical_ticks = 0
    choice_keys: list[str] = []
    for r in rows:
        choice_keys.append(str(r.get("choice_key", "")))
        # Recompute critical from logged body fields when present
        if (
            float(r.get("hunger", 0.0)) >= _CRITICAL_HUNGER
            or float(r.get("thirst", 0.0)) >= _CRITICAL_THIRST
            or float(r.get("fatigue", 0.0)) >= _CRITICAL_FATIGUE
        ):
            critical_ticks += 1
    summary = {
        "seed": seed,
        "condition": condition,
        "steps": steps,
        "n_ticks": len(rows),
        "mean_agency": sum(r["agency"] for r in rows) / n,
        "mean_spike_aligned": sum(r["spike_aligned"] for r in rows) / n,
        "pfc_veto_rate": sum(1 for r in rows if r["pfc_veto"]) / n,
        "inhibited_rate": sum(1 for r in rows if r["inhibited"]) / n,
        "remembered_rate": sum(1 for r in rows if r["remembered"]) / n,
        "mean_surprise": sum(r["surprise"] for r in rows) / n,
        "mean_drive_coherent": sum(r["drive_coherent"] for r in rows) / n,
        "mean_homeostatic_abs_dev": sum(r["homeostatic_abs_dev"] for r in rows) / n,
        "final_homeostatic_abs_dev": rows[-1]["homeostatic_abs_dev"] if rows else None,
        "agency_override_rate": agency_overrides / n,
        "action_entropy_bits": _action_entropy(choice_keys),
        "critical_state_tick_count": critical_ticks,
        "critical_state_tick_rate": critical_ticks / n,
        "profile": rows[0]["profile"] if rows else "",
        "n_neurons": rows[0]["n_neurons"] if rows else 0,
        "git_commit": _git_commit(),
        "timestamp_utc": _utc_now(),
        # Formal episode survival until death/termination is not defined in core.
        "survival_time": "MISSING_not_formalized",
    }
    return summary


def run_matrix(
    conditions: list[str],
    *,
    seeds: int,
    steps: int,
    out_dir: Path,
    write_jsonl: bool = False,
) -> list[dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    enable_experiment_gpu()
    summaries: list[dict[str, Any]] = []
    t0 = time.perf_counter()
    try:
        for cond in conditions:
            for seed in range(seeds):
                jsonl = out_dir / f"{cond}_s{seed}.jsonl" if write_jsonl else None
                print(f"  [{cond}] seed={seed} steps={steps}", flush=True)
                summary = run_condition_episode(
                    condition=cond, seed=seed, steps=steps, jsonl_path=jsonl
                )
                summaries.append(summary)
                print(
                    f"    agency={summary['mean_agency']:.4f} "
                    f"coh={summary['mean_drive_coherent']:.4f} "
                    f"hdev={summary['mean_homeostatic_abs_dev']:.4f} "
                    f"ovr={summary['agency_override_rate']:.2f}",
                    flush=True,
                )
    finally:
        release_experiment_gpu()

    write_summary_csv(out_dir / "seed_summaries.csv", summaries)
    meta = {
        "conditions": conditions,
        "seeds": seeds,
        "steps": steps,
        "profile_env": os.environ.get("CEREBRO_EXPERIMENT_PROFILE"),
        "git_commit": _git_commit(),
        "timestamp_utc": _utc_now(),
        "elapsed_sec": round(time.perf_counter() - t0, 2),
        "write_jsonl": write_jsonl,
        "note": "Study wrappers for reactive/no_homeostasis/td_direct/agency_break; not core defaults.",
    }
    (out_dir / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return summaries


def run_env_shift(*, seeds: int, out_dir: Path) -> list[dict[str, Any]]:
    """Reuse Arena transfer + discrimination patterns (compact)."""
    from experiments.arena.task_discrimination import run_discrimination_good_vs_dry
    from experiments.arena.task_transfer_fountain import run_transfer_fountain_arm

    out_dir.mkdir(parents=True, exist_ok=True)
    enable_experiment_gpu()
    rows: list[dict[str, Any]] = []
    try:
        for seed in range(seeds):
            for aff in (False, True):
                print(f"  transfer seed={seed} aff={aff}", flush=True)
                tr = run_transfer_fountain_arm(seed, affordances=aff)
                rows.append(
                    {
                        "task": "transfer_fountain",
                        "seed": seed,
                        "affordances": aff,
                        "condition": tr.get("condition", "aff_on" if aff else "aff_off"),
                        "phase1_success": (tr.get("exposure1") or {}).get("success"),
                        "phase1_ticks": (tr.get("exposure1") or {}).get("ticks_to_drink"),
                        "phase2_success": (tr.get("exposure2") or {}).get("success"),
                        "phase2_ticks": (tr.get("exposure2") or {}).get("ticks_to_drink"),
                        "phase2_thirst_delta": (tr.get("exposure2") or {}).get("thirst_delta"),
                        "git_commit": _git_commit(),
                        "timestamp_utc": _utc_now(),
                        "profile": os.environ.get("CEREBRO_EXPERIMENT_PROFILE", "compact"),
                    }
                )
                print(f"  discrimination seed={seed} aff={aff}", flush=True)
                di = run_discrimination_good_vs_dry(seed, affordances=aff)
                rows.append(
                    {
                        "task": "discrimination",
                        "seed": seed,
                        "affordances": aff,
                        "condition": di.get("condition", "aff_on" if aff else "aff_off"),
                        "drank_success": di.get("drank_success"),
                        "ticks": di.get("ticks"),
                        "preferred_good": di.get("preferred_good"),
                        "goal_is_good": di.get("goal_is_good"),
                        "git_commit": _git_commit(),
                        "timestamp_utc": _utc_now(),
                        "profile": os.environ.get("CEREBRO_EXPERIMENT_PROFILE", "compact"),
                    }
                )
                # Checkpoint after each seed×aff pair (crash-safe)
                (out_dir / "env_shift_raw.json").write_text(
                    json.dumps(rows, ensure_ascii=False, indent=2, default=str),
                    encoding="utf-8",
                )
    finally:
        release_experiment_gpu()

    # Flatten for CSV (union of keys — transfer vs discrimination schemas differ)
    all_keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in all_keys:
                all_keys.append(k)
    flat = []
    for r in rows:
        flat.append({k: ("" if r.get(k) is None else r.get(k, "")) for k in all_keys})
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "env_shift_seed_results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=all_keys)
        w.writeheader()
        w.writerows(flat)
    (out_dir / "env_shift_raw.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    return rows


def copy_historical_e1e3() -> None:
    src = ROOT / "experiments" / "results"
    dst = PF / "raw_results" / "historical"
    dst.mkdir(parents=True, exist_ok=True)
    names = [
        "e1_full_summary.csv",
        "e1_nopfc_summary.csv",
        "e1_nobind_summary.csv",
        "e1_nohippo_summary.csv",
        "e1_noaffect_summary.csv",
        "e2_llm_invariance.csv",
        "e3_sleep_recall.csv",
        "e4_sleep_selective.csv",
        "e5_grounding.csv",
        "e7_multimodal.csv",
        "arena_discrimination.json",
        "arena_thirst_unknown_water.csv",
        "bench_tick_gpu.csv",
        "bench_hw_notes.md",
    ]
    copied = []
    for name in names:
        p = src / name
        if p.exists():
            shutil.copy2(p, dst / name)
            copied.append(name)
    note = {
        "copied": copied,
        "source": str(src),
        "note": "Historical evidence as-is. E1–E3 are SCALE_10K_PROFILE, n=5 seeds. NOT re-run at 10k×20.",
        "e1e3_10k_x20_replication": "NOT RUN / deferred (see COMPUTE_ESTIMATE.md)",
        "timestamp_utc": _utc_now(),
        "git_commit": _git_commit(),
    }
    (dst / "HISTORICAL_COPY_NOTE.json").write_text(json.dumps(note, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["A", "B", "C", "D", "E10k_smoke", "all"], default="all")
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--profile", default="compact")
    parser.add_argument("--jsonl", action="store_true", help="Write per-tick JSONL (larger disk)")
    parser.add_argument(
        "--out-root",
        default="",
        help="Optional root under publication_finalization/raw_results/ "
        "(e.g. n20_compact). Empty = legacy paths baselines_A / agency_break_B / env_shift_C.",
    )
    args = parser.parse_args()

    os.environ.setdefault("CEREBRO_OLLAMA", "0")
    os.environ.setdefault("CEREBRO_SKIP_PROCESS_GUARD", "1")
    set_profile_env(args.profile)

    raw_base = PF / "raw_results"
    if args.out_root:
        raw_base = PF / "raw_results" / args.out_root
        raw_base.mkdir(parents=True, exist_ok=True)

    def _out(name: str) -> Path:
        return raw_base / name

    cfg = {
        "phase": args.phase,
        "seeds": args.seeds,
        "steps": args.steps,
        "profile": args.profile,
        "out_root": args.out_root or "(legacy raw_results/{baselines_A,agency_break_B,env_shift_C})",
        "git_commit": _git_commit(),
        "timestamp_utc": _utc_now(),
        "compute_policy": "COMPACT primary; see COMPUTE_ESTIMATE.md / EVIDENCE_GAP_FILL.md",
        "metrics_note": (
            "action_entropy_bits + critical_state_tick_* from tick logs; "
            "survival_time remains MISSING_not_formalized"
        ),
    }
    (PF / "configs" / "run_config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    # Also stash a copy beside this campaign when using out-root
    if args.out_root:
        (raw_base / "run_config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    if args.phase in ("A", "all"):
        print("=== Phase A: baselines ===", flush=True)
        run_matrix(
            ["full", "reactive", "nohippo", "no_homeostasis", "nopfc", "td_direct"],
            seeds=args.seeds,
            steps=args.steps,
            out_dir=_out("baselines_A"),
            write_jsonl=args.jsonl,
        )

    if args.phase in ("B", "all"):
        print("=== Phase B: agency-break ===", flush=True)
        run_matrix(
            ["full", "agency_break"],
            seeds=args.seeds,
            steps=args.steps,
            out_dir=_out("agency_break_B"),
            write_jsonl=args.jsonl,
        )

    if args.phase in ("C", "all"):
        print("=== Phase C: environmental shift ===", flush=True)
        run_env_shift(seeds=args.seeds, out_dir=_out("env_shift_C"))

    if args.phase in ("D", "all"):
        print("=== Phase D: historical E1–E3 copy ===", flush=True)
        copy_historical_e1e3()
        # Optional compact smoke (2 seeds) — cheap validation that runners still work
        print("=== Phase D smoke: E1-like compact 2 seeds ===", flush=True)
        run_matrix(
            ["full", "nopfc", "nohippo"],
            seeds=min(2, args.seeds),
            steps=min(40, args.steps),
            out_dir=PF / "raw_results" / "e1e3_smoke_D",
            write_jsonl=False,
        )
        (PF / "raw_results" / "e1e3_smoke_D" / "SMOKE_NOTE.txt").write_text(
            "Compact smoke only (2 seeds, short ticks). Historical 10k E1–E3 remain primary for those claims.\n"
            "Multi-seed 10k replication: NOT RUN / deferred.\n",
            encoding="utf-8",
        )

    if args.phase == "E10k_smoke":
        # Optional cheap 10k smoke: 2 seeds × 2 conditions (full vs nopfc). Not primary.
        print("=== Optional 10k smoke: full vs nopfc, 2 seeds ===", flush=True)
        set_profile_env("10k")
        smoke_dir = _out("e10k_smoke") if args.out_root else (PF / "raw_results" / "e10k_smoke")
        run_matrix(
            ["full", "nopfc"],
            seeds=min(2, args.seeds),
            steps=min(40, args.steps),
            out_dir=smoke_dir,
            write_jsonl=False,
        )
        (smoke_dir / "SMOKE_NOTE.txt").write_text(
            "Optional SCALE_10K smoke only (2 seeds × full/nopfc, short ticks).\n"
            "NOT a substitute for E1–E3 10k×20 replication. Primary A/B/C remain compact n=20.\n",
            encoding="utf-8",
        )

    print("Done.", flush=True)


if __name__ == "__main__":
    main()
