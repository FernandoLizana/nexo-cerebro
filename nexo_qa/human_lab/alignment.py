"""Behavioral alignment analyzer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nexo_qa.human_lab.path_similarity import normalized_levenshtein_similarity, sequence_overlap
from nexo_qa.human_lab.statistics import pearson_correlation


@dataclass
class AlignmentResult:
    outcome_alignment: float | None = None
    action_count_alignment: float | None = None
    path_alignment: float | None = None
    failure_alignment: float | None = None
    backtracking_alignment: float | None = None
    recovery_alignment: float | None = None
    abandonment_alignment: float | None = None
    perturbation_response_alignment: float | None = None
    n_pairs: int = 0
    coverage: dict[str, Any] = field(default_factory=dict)
    disclaimer: str = "alignment on matched cells — not human validation unless real data"

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome_alignment": self.outcome_alignment,
            "action_count_alignment": self.action_count_alignment,
            "path_alignment": self.path_alignment,
            "failure_alignment": self.failure_alignment,
            "backtracking_alignment": self.backtracking_alignment,
            "recovery_alignment": self.recovery_alignment,
            "abandonment_alignment": self.abandonment_alignment,
            "perturbation_response_alignment": self.perturbation_response_alignment,
            "n_pairs": self.n_pairs,
            "coverage": dict(self.coverage),
            "disclaimer": self.disclaimer,
        }


class BehavioralAlignmentAnalyzer:
    def analyze(
        self,
        *,
        human_summaries: list[dict[str, Any]],
        nexo_summaries: list[dict[str, Any]],
        human_paths: dict[str, list[str]] | None = None,
        nexo_paths: dict[str, list[str]] | None = None,
    ) -> AlignmentResult:
        n = min(len(human_summaries), len(nexo_summaries))
        if n == 0:
            return AlignmentResult(n_pairs=0, coverage={"reason": "no_pairs"})

        h_out = [1.0 if s.get("completed") else 0.0 for s in human_summaries[:n]]
        n_out = [1.0 if s.get("completed") else 0.0 for s in nexo_summaries[:n]]
        outcome = sum(1 for a, b in zip(h_out, n_out) if a == b) / n

        h_actions = [float(s.get("action_count", 0)) for s in human_summaries[:n]]
        n_actions = [float(s.get("action_count", 0)) for s in nexo_summaries[:n]]
        action_corr = pearson_correlation(h_actions, n_actions)

        path_scores: list[float] = []
        if human_paths and nexo_paths:
            for i in range(n):
                hid = human_summaries[i].get("human_run_id", str(i))
                nid = nexo_summaries[i].get("run_id", str(i))
                hp = human_paths.get(str(hid), [])
                np = nexo_paths.get(str(nid), [])
                path_scores.append(normalized_levenshtein_similarity(hp, np))
        path_align = sum(path_scores) / len(path_scores) if path_scores else None

        h_back = [float(s.get("backtracks", 0)) for s in human_summaries[:n]]
        n_back = [float(s.get("backtracks", 0)) for s in nexo_summaries[:n]]

        return AlignmentResult(
            outcome_alignment=round(outcome, 4),
            action_count_alignment=action_corr,
            path_alignment=round(path_align, 4) if path_align is not None else None,
            failure_alignment=pearson_correlation(
                [float(s.get("validation_errors", 0)) for s in human_summaries[:n]],
                [float((s.get("failure_count") or 0)) for s in nexo_summaries[:n]],
            ),
            backtracking_alignment=pearson_correlation(h_back, n_back),
            recovery_alignment=pearson_correlation(
                [float(s.get("recovery_episodes", 0)) for s in human_summaries[:n]],
                [float(s.get("recovery_episodes", 0)) for s in nexo_summaries[:n]],
            ),
            abandonment_alignment=sum(
                1
                for a, b in zip(
                    [bool(s.get("abandoned")) for s in human_summaries[:n]],
                    [bool(s.get("abandoned")) for s in nexo_summaries[:n]],
                )
                if a == b
            )
            / n,
            n_pairs=n,
            coverage={"matched_cells": n},
        )
