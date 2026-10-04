"""Goal relevance — heuristic token/entity match, not human-calibrated."""

from __future__ import annotations

import re

from nexo_qa.goals.models import Goal
from nexo_qa.goals.parser import SYNONYMS

STOPWORDS = frozenset({"el", "la", "de", "y", "the", "a", "to", "en", "un", "una", "tu", "your"})


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-záéíóúü0-9]+", text.lower()) if t not in STOPWORDS and len(t) > 1}


def _expand_tokens(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for token in list(tokens):
        for canonical, variants in SYNONYMS.items():
            if token in variants or token == canonical:
                expanded.add(canonical)
                expanded.update(variants)
    return expanded


def goal_relevance_for_text(goal: Goal, text: str) -> float:
    """Relevance of arbitrary text (percept label, action label) to active goal."""
    if not text:
        return 0.0
    text_tokens = _expand_tokens(_tokens(text))
    goal_tokens = _expand_tokens(_tokens(goal.description))
    goal_tokens.update(_tokens(" ".join(goal.entities.values())))
    goal_tokens.update(_tokens(" ".join(str(v) for v in goal.constraints.values() if v not in (True, False))))
    if goal.active_subgoal:
        goal_tokens.update(_tokens(goal.active_subgoal.replace("_", " ")))
    if not goal_tokens:
        return 0.0
    overlap = len(text_tokens & goal_tokens)
    if overlap == 0:
        for entity_val in goal.entities.values():
            if entity_val and entity_val.lower() in text.lower():
                return 0.65
        return 0.0
    return float(min(1.0, 0.25 + 0.2 * overlap))


def goal_relevance_for_action(goal: Goal, action_label: str, *, affordance: str = "") -> float:
    score = goal_relevance_for_text(goal, action_label)
    plan = goal.entities.get("plan", "")
    if plan and plan.lower() in action_label.lower():
        score = max(score, 0.75)
    if goal.goal_type == "find_pricing" and any(t in action_label.lower() for t in ("plan", "pro", "básico", "basico", "precio")):
        score = max(score, 0.5)
    if affordance == "navigable" and goal.goal_type == "navigation":
        score = max(score, 0.4)
    if affordance == "navigable" and goal.active_subgoal in ("explorar_sitio", "localizar_seccion_precios"):
        score = max(score, 0.35)
    return float(min(1.0, score))


def goal_relevance_map(goal: Goal, actions: tuple[tuple[str, str, str], ...]) -> dict[str, float]:
    """Map action_id → relevance. actions: (id, label, affordance)."""
    return {
        action_id: goal_relevance_for_action(goal, label, affordance=affordance)
        for action_id, label, affordance in actions
    }
