"""Selección Go/No-Go con trazas de hábito."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from nexo.prefrontal.contestant import DeliberationResult


@dataclass
class ActionGate:
    """Ganglios basales simplificados sobre acciones simbólicas."""

    no_go_threshold: float = 0.12
    habit_decay: float = 0.995
    habit_gain: float = 0.06
    habits: dict[str, float] = field(default_factory=dict)

    def select(
        self,
        *,
        candidates: tuple[str, ...],
        base_scores: dict[str, float],
        deliberation: DeliberationResult | None,
        retrieved_boost: dict[str, float],
        td_biases: dict[str, float] | None = None,
        rng: np.random.Generator,
        executive_gain: float = 1.0,
    ) -> tuple[str, float, dict[str, float], bool]:
        scores = dict(base_scores)
        vetoed = False

        for action in candidates:
            scores[action] = scores.get(action, 0.0) + self.habits.get(action, 0.0) * 0.35
            scores[action] += retrieved_boost.get(action, 0.0)
            if td_biases:
                scores[action] += td_biases.get(action, 0.0)

        if deliberation is not None:
            choice = deliberation.choice_key
            if choice in scores:
                scores[choice] += (0.2 + 0.5 * deliberation.confidence) * executive_gain
            if deliberation.inhibited and deliberation.limbic_winner_key in scores:
                scores[deliberation.limbic_winner_key] -= 0.25 * deliberation.conflict * executive_gain
                vetoed = deliberation.pfc_veto

        for action in candidates:
            scores[action] += float(rng.normal(0.0, 0.025))

        if not scores:
            return "rest", 0.1, {}, vetoed

        ranked = sorted(scores.items(), key=lambda x: -x[1])
        best, best_score = ranked[0]
        second = ranked[1][1] if len(ranked) > 1 else best_score - 0.1

        if best_score < self.no_go_threshold:
            return "rest", 0.12, scores, vetoed

        margin = best_score - second
        confidence = float(max(0.1, min(0.99, 0.45 + margin * 0.35)))

        self.habits[best] = min(3.0, self.habits.get(best, 0.0) + self.habit_gain)
        for action in list(self.habits):
            self.habits[action] *= self.habit_decay
            if self.habits[action] < 0.01:
                del self.habits[action]

        return best, confidence, scores, vetoed

    def max_habit(self) -> float:
        return max(self.habits.values()) if self.habits else 0.0
