"""Deliberación prefrontal sobre ActionSchema (P1) con fallback RoomWorld."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from nexo.core.action_schema import ActionSchema
from nexo.core.legacy_action_adapter import ROOM_ACTION_SCHEMAS, drive_for_affordance
from nexo.prefrontal.contestant import ActionContestant, DeliberationResult


@dataclass(frozen=True, slots=True)
class _SchemaRow:
    key: str
    drive: str
    label: str
    affordance: str | None = None


def _rows_from_legacy_catalog(candidates: tuple[str, ...]) -> list[_SchemaRow]:
    return [
        _SchemaRow(key=row["key"], drive=row["drive"], label=row["label"])
        for row in ROOM_ACTION_SCHEMAS
        if row["key"] in candidates
    ]


def _rows_from_action_schemas(
    candidates: tuple[str, ...],
    schemas: Sequence[ActionSchema],
) -> list[_SchemaRow]:
    by_id = {schema.id: schema for schema in schemas}
    rows: list[_SchemaRow] = []
    for key in candidates:
        schema = by_id.get(key)
        if schema is None:
            continue
        drive = (schema.expected_effect or drive_for_affordance(schema.affordance) or "").strip()
        rows.append(
            _SchemaRow(
                key=schema.id,
                drive=drive,
                label=schema.label,
                affordance=schema.affordance,
            )
        )
    return rows


def _is_exploratory(row: _SchemaRow) -> bool:
    if row.key in ("inspect_distractor", "explore"):
        return True
    if row.drive == "curiosity":
        return True
    return row.affordance in ("inspectable", "navigable")


def _is_consumable(row: _SchemaRow) -> bool:
    return row.key == "eat" or row.drive == "hunger" or row.affordance == "consumable"


def _is_restorative(row: _SchemaRow) -> bool:
    return row.key == "rest" or row.drive == "rest" or row.affordance == "restorable"


def _is_avoidant(row: _SchemaRow) -> bool:
    return row.key == "flee" or row.drive == "safety" or row.affordance == "avoidable"


@dataclass
class PrefrontalDeliberator:
    """Competencia límbica vs PFC sobre acciones disponibles."""

    pfc_inhibition_strength: float = 0.55
    low_energy_threshold: float = 0.35
    last: DeliberationResult = field(default_factory=DeliberationResult, init=False)

    def run(
        self,
        *,
        candidates: tuple[str, ...],
        drives: dict[str, float],
        wm_items: dict[str, float],
        goals: tuple[str, ...],
        plan_action: str | None,
        energy: float,
        safety_need: float,
        habit_bias: dict[str, float],
        workspace_bias: dict[str, float] | None = None,
        action_schemas: Sequence[ActionSchema] | None = None,
        goal_relevance: dict[str, float] | None = None,
        persona_modifiers: dict[str, float] | None = None,
    ) -> DeliberationResult:
        if action_schemas is None:
            rows = _rows_from_legacy_catalog(candidates)
        else:
            rows = _rows_from_action_schemas(candidates, action_schemas)

        relevance = goal_relevance or {}
        mods = persona_modifiers or {}
        risk_by_id: dict[str, float] = {}
        if action_schemas is not None:
            for schema in action_schemas:
                if schema.risk is not None:
                    risk_by_id[schema.id] = float(schema.risk)

        contestants: list[ActionContestant] = []

        for row in rows:
            key = row.key
            drive_key = row.drive
            limbic = float(drives.get(drive_key, 0.0)) if drive_key else 0.0
            if _is_avoidant(row) and safety_need > 0.4:
                limbic = max(limbic, safety_need * 0.9)
            if _is_consumable(row) and energy < self.low_energy_threshold:
                limbic = max(limbic, (1.0 - energy) * 0.8)

            rel = float(relevance.get(key, 0.0))
            pfc = self._pfc_score(
                row,
                wm_items,
                goals,
                plan_action,
                energy,
                relevance=rel,
                persona_modifiers=mods,
            )
            habit = float(habit_bias.get(key, 0.0))
            ws = float((workspace_bias or {}).get(key, 0.0))
            net = 0.55 * limbic + 0.35 * pfc + 0.10 * habit + 0.25 * ws
            net += 0.22 * rel
            risk = risk_by_id.get(key)
            if risk is not None:
                net -= float(mods.get("risk_aversion", 0.0)) * risk
            contestants.append(
                ActionContestant(
                    key=key,
                    label=row.label,
                    drive=drive_key or "none",
                    limbic=limbic,
                    pfc=pfc,
                    habit=habit,
                    net=net,
                )
            )

        if not contestants:
            return DeliberationResult()

        limbic_winner = max(contestants, key=lambda c: c.limbic)
        pfc_winner = max(contestants, key=lambda c: c.pfc)
        winner = max(contestants, key=lambda c: c.net)

        conflict = abs(limbic_winner.net - pfc_winner.net)
        inhibited = False
        pfc_veto = False

        limbic_row = next(r for r in rows if r.key == limbic_winner.key)
        if (
            limbic_winner.key != pfc_winner.key
            and energy < self.low_energy_threshold
            and _is_exploratory(limbic_row)
            and pfc_winner.pfc >= 0.35
        ):
            winner = pfc_winner
            inhibited = True
            pfc_veto = True

        if plan_action and plan_action in candidates:
            for c in contestants:
                if c.key == plan_action:
                    c.net += 0.18
            winner = max(contestants, key=lambda c: c.net)

        winner.selected = True
        confidence = float(
            min(0.99, max(0.15, 0.35 + winner.net * 0.4 + (0.1 if not inhibited else 0.05)))
        )
        # High risk aversion lowers confidence on risky chosen actions.
        winner_risk = risk_by_id.get(winner.key)
        if winner_risk is not None and winner_risk > 0.0:
            confidence *= max(0.15, 1.0 - float(mods.get("risk_aversion", 0.0)) * winner_risk)

        result = DeliberationResult(
            choice_key=winner.key,
            confidence=confidence,
            conflict=conflict,
            limbic_winner_key=limbic_winner.key,
            pfc_winner_key=pfc_winner.key,
            inhibited=inhibited,
            pfc_veto=pfc_veto,
            contestants=contestants,
        )
        self.last = result
        return result

    def _pfc_score(
        self,
        row: _SchemaRow,
        wm_items: dict[str, float],
        goals: tuple[str, ...],
        plan_action: str | None,
        energy: float,
        *,
        relevance: float = 0.0,
        persona_modifiers: dict[str, float] | None = None,
    ) -> float:
        # Intentionally ignores ActionSchema.metadata (selectors, coordinates, …).
        mods = persona_modifiers or {}
        action = row.key
        score = 0.12
        if action in wm_items:
            score += 0.25 * wm_items[action]
        if _is_consumable(row) and energy < 0.4:
            score += 0.35
        if _is_restorative(row) and energy < 0.25:
            score += 0.2
        if _is_avoidant(row) and "survive" in goals:
            score += 0.15
        if plan_action == action:
            score += 0.22
        if _is_exploratory(row) and energy < 0.35:
            if row.key == "inspect_distractor":
                score -= 0.25
            elif row.affordance == "inspectable":
                score -= 0.15
        literacy = float(mods.get("digital_literacy", 0.5))
        semantic = float(mods.get("semantic_confidence", 0.5))
        score += 0.35 * relevance * (0.5 + 0.5 * literacy)
        score *= 0.7 + 0.6 * semantic
        if float(mods.get("metacognitive_sensitivity", 0.0)) > 0.7 and row.affordance == "inspectable":
            score += 0.08
        return float(max(0.0, min(1.2, score)))
