"""Deterministic seed derivation — reordering invariant."""

from __future__ import annotations

import hashlib


def derive_child_seed(
    master_seed: int,
    *,
    cohort_id: str,
    task_id: str,
    sample_index: int,
    persona_id: str,
    condition_set_id: str,
) -> int:
    """Hash-based child seed — independent of execution order."""
    payload = f"{master_seed}|{cohort_id}|{task_id}|{sample_index}|{persona_id}|{condition_set_id}"
    digest = hashlib.sha256(payload.encode()).hexdigest()
    return int(digest[:8], 16)


def derive_paired_seed(
    master_seed: int,
    *,
    pair_id: str,
    task_id: str,
    persona_id: str,
) -> int:
    """Paired runs share seed — condition is NOT part of hash."""
    payload = f"{master_seed}|pair|{pair_id}|{task_id}|{persona_id}"
    digest = hashlib.sha256(payload.encode()).hexdigest()
    return int(digest[:8], 16)


def derive_run_id(
    spec_hash: str,
    cohort_id: str,
    task_id: str,
    persona_id: str,
    seed: int,
    condition_set_id: str,
    sample_index: int,
) -> str:
    payload = f"{spec_hash}|{cohort_id}|{task_id}|{persona_id}|{seed}|{condition_set_id}|{sample_index}"
    return f"run-{hashlib.sha256(payload.encode()).hexdigest()[:12]}"
