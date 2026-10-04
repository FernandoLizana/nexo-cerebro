"""Failure taxonomy validation against human annotations."""

from __future__ import annotations

from typing import Any


def confusion_matrix(
    human_labels: list[str],
    predicted_labels: list[str],
    *,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    labels = labels or sorted(set(human_labels) | set(predicted_labels))
    matrix = {a: {b: 0 for b in labels} for a in labels}
    for h, p in zip(human_labels, predicted_labels):
        if h in matrix and p in matrix[h]:
            matrix[h][p] += 1
    return {"labels": labels, "matrix": matrix}


def taxonomy_metrics(human_labels: list[str], predicted_labels: list[str]) -> dict[str, Any]:
    if not human_labels:
        return {"status": "NO_ANNOTATIONS", "n": 0}
    labels = sorted(set(human_labels) | set(predicted_labels))
    tp = fp = fn = 0
    for h, p in zip(human_labels, predicted_labels):
        if h == p:
            tp += 1
        else:
            fp += 1
            fn += 1
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-9, precision + recall)
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "confusion": confusion_matrix(human_labels, predicted_labels, labels=labels),
        "n": len(human_labels),
    }
