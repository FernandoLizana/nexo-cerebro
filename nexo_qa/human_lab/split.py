"""Train/holdout splits — grouped by participant."""

from __future__ import annotations

from typing import Any


def grouped_train_holdout_split(
    participant_ids: list[str],
    *,
    holdout_fraction: float = 0.2,
    seed: int = 42,
) -> dict[str, list[str]]:
    """Split participants — same ID never in both train and holdout."""
    import hashlib

    ordered = sorted(participant_ids, key=lambda p: hashlib.sha256(f"{seed}|{p}".encode()).hexdigest())
    n_holdout = max(1, int(len(ordered) * holdout_fraction)) if len(ordered) >= 5 else 0
    holdout = ordered[:n_holdout] if n_holdout else []
    train = [p for p in ordered if p not in holdout]
    return {"train": train, "holdout": holdout}


def leave_one_participant_out(participant_ids: list[str]) -> list[dict[str, list[str]]]:
    folds: list[dict[str, list[str]]] = []
    for held in participant_ids:
        folds.append({"holdout": [held], "train": [p for p in participant_ids if p != held]})
    return folds
