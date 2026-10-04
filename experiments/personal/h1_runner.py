"""Utilidades compartidas — experimentos H1 memoria."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE
from nexo.ablation.profiles import ABLATION_REGISTRY
from nexo.behavioral.agency_audit import summarize_agency_audit
from nexo.behavioral.causal_certificate import summarize_causal_certificates
from nexo.behavioral.memory_bridge import summarize_memory_bridge
from nexo.behavioral.memory_unification import summarize_memory_unification
from nexo.demo.day_in_the_life import build_day_timeline, day_in_the_life_ticks
from nexo.demo.flask_unified import FlaskUnifiedSession
from nexo.demo.legacy_sync import sync_integrated_body_from_legacy
from nexo.demo.memory_unification import _episode_to_pattern
from nexo.integrated_runtime import _repo_root, runtime_from_config
from nexo.memory.hippocampus.store import HippocampalStore


def _prepare_brain(*, seed: int, state_dir: Path) -> InfantApeBrain:
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=state_dir,
        headless=True,
        auto_save=False,
        seed=seed,
    )
    brain.world.ensure_home()
    brain.ensure_companion()
    brain.hypothalamus.energy = 0.22
    brain.hypothalamus.hunger = 0.82
    return brain


def run_h1_interactive(
    *,
    seed: int = 42,
    ticks: int | None = None,
    ablation_id: str = "integrated_full",
    config_path: Path | None = None,
) -> dict[str, Any]:
    import tempfile

    root = _repo_root()
    cfg_path = config_path or root / "configs/nexo/integrated_v80.yaml"
    sd = Path(tempfile.mkdtemp(prefix=f"nexo_h1_{ablation_id}_"))
    brain = _prepare_brain(seed=seed, state_dir=sd)
    rt = runtime_from_config(cfg_path, legacy_brain=brain, ablation_id=ablation_id)
    sync_integrated_body_from_legacy(brain, rt)
    session = FlaskUnifiedSession(brain=brain, runtime=rt, config_path=cfg_path)
    session.bind_worlds()

    n = ticks or day_in_the_life_ticks(
        simulated_hours=24.0,
        seconds_per_tick=rt.clock.seconds_per_tick,
    )
    last_sidecar: dict[str, Any] = {}
    for _ in range(n):
        last_sidecar = session.runtime.run(1)
        session.bind_worlds()
        session._tick_count += 1

    store = rt.scheduler.config.get("hippocampal_store")
    consolidator = rt.scheduler.config.get("memory_consolidator")
    legacy_store = getattr(brain, "memory_store", None)
    encoded = [
        ev for ev in rt.state_store.event_log if ev.event_type == "memory.encoded"
    ]
    consolidated = [
        ev for ev in rt.state_store.event_log if ev.event_type == "memory.consolidated"
    ]
    unified = [
        ev
        for ev in rt.state_store.event_log
        if ev.event_type == "memory.unified" and ev.payload.get("promoted")
    ]

    return {
        "ablation_id": ablation_id,
        "seed": seed,
        "ticks": n,
        "simulated_hours": round(rt.clock.simulation_seconds / 3600.0, 3),
        "memory_unification": summarize_memory_unification(rt),
        "memory_bridge": summarize_memory_bridge(rt),
        "causal_certificates": summarize_causal_certificates(rt),
        "agency_audit": summarize_agency_audit(rt),
        "timeline": build_day_timeline(rt),
        "encoding": {
            "memory_encoded_events": len(encoded),
            "hippocampal_episodes": len(store.episodes) if store else 0,
            "consolidated_ids": len(getattr(consolidator, "consolidated_ids", set())),
            "consolidation_events": len(consolidated),
            "promoted_count": len(unified),
            "legacy_memory_count": int(getattr(legacy_store, "total_count", lambda: 0)()),
        },
        "runtime_summary": {
            "sleep_phase": last_sidecar.get("sleep_phase"),
            "sleep_cycles": last_sidecar.get("sleep_cycles"),
            "memory_consolidations": last_sidecar.get("memory_consolidations"),
            "hippocampal_episodes": last_sidecar.get("hippocampal_episodes"),
            "actions_taken": last_sidecar.get("actions_taken", [])[-12:],
        },
    }


def _count_retrievals(rt: Any) -> int:
    return sum(1 for ev in rt.state_store.event_log if ev.event_type == "memory.retrieved")


def _promoted_episode_map(rt: Any) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for ev in rt.state_store.event_log:
        if ev.event_type != "memory.unified" or not ev.payload.get("promoted"):
            continue
        episode_id = str(ev.payload.get("episode_id", ""))
        key = str(ev.payload.get("key", ""))
        if episode_id and key:
            mapping[episode_id] = key
    return mapping


def _legacy_native_keys(brain: Any) -> list[str]:
    store = getattr(brain, "memory_store", None)
    if store is None:
        return []
    keys: list[str] = []
    for mem in getattr(store, "_hot", []) or []:
        key = str(mem.get("key", ""))
        if key and not key.startswith("hippo_"):
            keys.append(key)
    return keys


def direct_recall_probe(
    brain: Any,
    store: HippocampalStore,
    consolidator: Any,
    *,
    promoted_map: dict[str, str],
    seed: int = 42,
) -> dict[str, Any]:
    import numpy as np

    legacy = getattr(brain, "memory_store", None)
    if legacy is None or not store.episodes:
        return {"n_probes": 0, "hippo_recall_rate": 0.0, "promoted_recall_rate": 0.0, "legacy_native_rate": 0.0}

    consolidated_ids = getattr(consolidator, "consolidated_ids", set())
    probe_items: list[tuple[Any | None, str, str]] = []
    for episode_id, key in list(promoted_map.items())[:15]:
        ep = next((e for e in store.episodes if e.episode_id == episode_id), None)
        probe_items.append((ep, episode_id, key))
    if not probe_items:
        for ep in store.episodes:
            if ep.episode_id in consolidated_ids:
                probe_items.append((ep, ep.episode_id, promoted_map.get(ep.episode_id, "")))
        probe_items = probe_items[:15]
    if not probe_items:
        for ep in store.episodes[-10:]:
            probe_items.append((ep, ep.episode_id, promoted_map.get(ep.episode_id, "")))
    rng = np.random.default_rng(seed)

    hippo_hits = 0
    promoted_hits = 0
    native_hits = 0
    probe_rows: list[dict[str, Any]] = []
    native_keys = _legacy_native_keys(brain)

    for ep, episode_id, expected_key in probe_items:
        if ep is None:
            mem = next((m for m in getattr(legacy, "_hot", []) if m.get("key") == expected_key), None)
            if mem is None or mem.get("pattern") is None:
                continue
            pattern = np.asarray(mem["pattern"], dtype=np.float32)
            body = mem.get("body") or {}
            best_hippo = 0.0
            hippo_hit = False
        else:
            cue = ep.cue_vector()
            partial = cue[: max(2, len(cue) // 2)]
            hippo_ret = store.retrieve_partial(partial, rng=rng, top_k=3)
            best_hippo = max(
                (sim for cand, sim in hippo_ret if cand.episode_id == ep.episode_id),
                default=0.0,
            )
            hippo_hit = best_hippo >= 0.35
            pattern = _episode_to_pattern(ep, int(getattr(legacy, "pattern_dim", 128)))
            body = {}
            if ep.body_context and len(ep.body_context) >= 3:
                body = {
                    "energy": float(ep.body_context[0]),
                    "fatigue": float(ep.body_context[1]),
                    "pain": float(ep.body_context[2]),
                }
        leg = legacy.recall(pattern, body=body or None, room="integrated", threshold=0.22, brain=brain)
        expected_key = expected_key or promoted_map.get(episode_id, "")
        promoted_hit = bool(
            leg
            and (
                (expected_key and str(leg.get("key", "")) == expected_key)
                or (
                    str(leg.get("key", "")).startswith("hippo_")
                    and episode_id in str(leg.get("key", ""))
                )
            )
        )

        native_hit = False
        native_sim = 0.0
        if native_keys:
            ref_key = native_keys[min(len(probe_rows), len(native_keys) - 1)]
            ref_mem = next((m for m in getattr(legacy, "_hot", []) if m.get("key") == ref_key), None)
            if ref_mem and ref_mem.get("pattern") is not None:
                native_pattern = np.asarray(ref_mem["pattern"], dtype=np.float32)
                native_leg = legacy.recall(
                    native_pattern,
                    body=ref_mem.get("body") or None,
                    room=str(ref_mem.get("room", "casa")),
                    threshold=0.18,
                    brain=brain,
                )
                native_hit = bool(
                    native_leg and not str(native_leg.get("key", "")).startswith("hippo_")
                )
                native_sim = float(native_leg.get("similarity", 0.0)) if native_leg else 0.0

        hippo_hits += int(hippo_hit)
        promoted_hits += int(promoted_hit)
        native_hits += int(native_hit)
        probe_rows.append(
            {
                "episode_id": episode_id,
                "promoted_key": expected_key or None,
                "hippo_similarity": round(best_hippo, 4),
                "hippo_hit": hippo_hit,
                "promoted_hit": promoted_hit,
                "legacy_native_hit": native_hit,
                "legacy_native_similarity": round(native_sim, 4),
            }
        )

    n = max(len(probe_rows), 1)
    return {
        "n_probes": len(probe_rows),
        "hippo_recall_rate": round(hippo_hits / n, 4),
        "promoted_recall_rate": round(promoted_hits / n, 4),
        "legacy_native_rate": round(native_hits / n, 4),
        "sample_probes": probe_rows[:6],
    }


def _inject_store_state(target_rt: Any, source_rt: Any) -> None:
    src_store: HippocampalStore | None = source_rt.scheduler.config.get("hippocampal_store")
    dst_store: HippocampalStore | None = target_rt.scheduler.config.get("hippocampal_store")
    src_cons = source_rt.scheduler.config.get("memory_consolidator")
    dst_cons = target_rt.scheduler.config.get("memory_consolidator")
    if src_store and dst_store:
        dst_store.episodes = list(src_store.episodes)
    if src_cons and dst_cons:
        dst_cons.consolidated_ids = set(src_cons.consolidated_ids)


def run_h1_retention(
    *,
    seed: int = 42,
    acquisition_ticks: int | None = None,
    delay_ticks: int = 48,
    probe_ticks: int = 24,
) -> dict[str, Any]:
    import tempfile

    from nexo.interventions.profiles import apply_lesion_profile

    root = _repo_root()
    cfg_path = root / "configs/nexo/integrated_v80.yaml"
    sd = Path(tempfile.mkdtemp(prefix="nexo_h1_retention_"))
    brain = _prepare_brain(seed=seed, state_dir=sd)
    rt = runtime_from_config(cfg_path, legacy_brain=brain, ablation_id="integrated_full")
    sync_integrated_body_from_legacy(brain, rt)
    session = FlaskUnifiedSession(brain=brain, runtime=rt, config_path=cfg_path)
    session.bind_worlds()

    n_acquire = acquisition_ticks or day_in_the_life_ticks(
        simulated_hours=24.0,
        seconds_per_tick=rt.clock.seconds_per_tick,
    )
    for _ in range(n_acquire):
        rt.run(1)
        session.bind_worlds()

    store: HippocampalStore = rt.scheduler.config["hippocampal_store"]
    consolidator = rt.scheduler.config["memory_consolidator"]
    promoted_map = _promoted_episode_map(rt)
    acquisition_encoding = {
        "hippocampal_episodes": len(store.episodes),
        "consolidated_ids": len(consolidator.consolidated_ids),
        "promoted_count": len(promoted_map),
        "legacy_memory_count": int(getattr(brain.memory_store, "total_count", lambda: 0)()),
    }

    for _ in range(delay_ticks):
        rt.run(1)

    recall_after_delay = direct_recall_probe(
        brain,
        store,
        consolidator,
        promoted_map=promoted_map,
        seed=seed,
    )

    retrievals_before = _count_retrievals(rt)
    for _ in range(probe_ticks):
        rt.run(1)
    integrated_retrievals = _count_retrievals(rt) - retrievals_before

    apply_lesion_profile("lesion_sever_hippo_pfc", rt.scheduler.router.lesions)
    retrievals_before_lesion = _count_retrievals(rt)
    for _ in range(probe_ticks):
        rt.run(1)
    lesioned_retrievals = _count_retrievals(rt) - retrievals_before_lesion

    rt_ablated = runtime_from_config(cfg_path, legacy_brain=brain, ablation_id="abl_no_memory")
    sync_integrated_body_from_legacy(brain, rt_ablated)
    _inject_store_state(rt_ablated, rt)
    retrievals_before_ablation = _count_retrievals(rt_ablated)
    for _ in range(probe_ticks):
        rt_ablated.run(1)
    ablated_retrievals = _count_retrievals(rt_ablated) - retrievals_before_ablation

    recall_ablated = direct_recall_probe(
        brain,
        rt_ablated.scheduler.config["hippocampal_store"],
        rt_ablated.scheduler.config["memory_consolidator"],
        promoted_map=promoted_map,
        seed=seed + 1,
    )

    return {
        "seed": seed,
        "acquisition_ticks": n_acquire,
        "delay_ticks": delay_ticks,
        "probe_ticks": probe_ticks,
        "acquisition": acquisition_encoding,
        "recall_after_delay": recall_after_delay,
        "runtime_probe": {
            "integrated_retrievals": integrated_retrievals,
            "lesioned_retrievals": lesioned_retrievals,
            "lesion_retention_ratio": round(
                lesioned_retrievals / max(integrated_retrievals, 1), 4
            ),
            "abl_no_memory_retrievals": ablated_retrievals,
        },
        "recall_under_ablation": recall_ablated,
        "retention_summary": {
            "hippo_channel": recall_after_delay["hippo_recall_rate"],
            "promoted_channel": recall_after_delay["promoted_recall_rate"],
            "legacy_native_channel": recall_after_delay["legacy_native_rate"],
            "hippo_survives_ablation": recall_ablated["hippo_recall_rate"],
            "promoted_survives_ablation": recall_ablated["promoted_recall_rate"],
        },
    }


def export_payload(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path)}


def run_h1_comparison(*, seed: int = 42, ticks: int | None = None) -> dict[str, Any]:
    conditions = ("integrated_full", "abl_no_memory")
    runs: dict[str, Any] = {}
    for ablation_id in conditions:
        if ablation_id not in ABLATION_REGISTRY:
            continue
        runs[ablation_id] = run_h1_interactive(seed=seed, ticks=ticks, ablation_id=ablation_id)

    full = runs.get("integrated_full", {})
    no_mem = runs.get("abl_no_memory", {})
    full_enc = full.get("encoding", {})
    no_mem_enc = no_mem.get("encoding", {})

    return {
        "seed": seed,
        "conditions": list(conditions),
        "runs": runs,
        "comparison": {
            "hippocampal_delta": full_enc.get("hippocampal_episodes", 0)
            - no_mem_enc.get("hippocampal_episodes", 0),
            "promotion_delta": full_enc.get("promoted_count", 0)
            - no_mem_enc.get("promoted_count", 0),
            "legacy_memory_delta": full_enc.get("legacy_memory_count", 0)
            - no_mem_enc.get("legacy_memory_count", 0),
            "integrated_full_promoted": full_enc.get("promoted_count", 0),
            "abl_no_memory_promoted": no_mem_enc.get("promoted_count", 0),
        },
    }
