"""Puerto único de emisión de decisiones con procedencia auditable."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Sequence


class DecisionSource(str, Enum):
    PREFRONTAL_DELIBERATION = "brain.deliberation.PrefrontalDeliberation.run"


ALLOWED_DECISION_SOURCES = frozenset({DecisionSource.PREFRONTAL_DELIBERATION.value})


@dataclass(frozen=True)
class Decision:
    choice_key: str
    selected_by: str
    tick: int
    seed: int
    config_hash: str
    candidate_scores: tuple[tuple[str, float], ...]
    limbic_winner_key: str = ""
    pfc_winner_key: str = ""
    inhibited: bool = False
    margin: float = 0.0
    legacy_agency_score: float = 0.0

    def __post_init__(self) -> None:
        if self.selected_by not in ALLOWED_DECISION_SOURCES:
            raise ValueError(f"selected_by no autorizado: {self.selected_by!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "choice_key": self.choice_key,
            "selected_by": self.selected_by,
            "tick": self.tick,
            "seed": self.seed,
            "config_hash": self.config_hash,
            "candidate_scores": list(self.candidate_scores),
            "limbic_winner_key": self.limbic_winner_key,
            "pfc_winner_key": self.pfc_winner_key,
            "inhibited": self.inhibited,
            "margin": self.margin,
            "legacy_agency_score": self.legacy_agency_score,
        }


class DecisionPort:
    PRIMARY = DecisionSource.PREFRONTAL_DELIBERATION.value

    @staticmethod
    def commit(
        *,
        choice_key: str,
        tick: int,
        seed: int,
        config_hash: str,
        contestants: Sequence[Any],
        limbic_winner_key: str,
        pfc_winner_key: str,
        inhibited: bool,
        margin: float,
        legacy_agency_score: float,
        selected_by: str = PRIMARY,
    ) -> Decision:
        if selected_by not in ALLOWED_DECISION_SOURCES:
            raise ValueError(f"Origen de decisión rechazado: {selected_by!r}")
        scores = tuple((str(getattr(c, "key", "")), float(getattr(c, "net", 0.0))) for c in contestants)
        return Decision(
            choice_key=choice_key,
            selected_by=selected_by,
            tick=tick,
            seed=seed,
            config_hash=config_hash,
            candidate_scores=scores,
            limbic_winner_key=limbic_winner_key,
            pfc_winner_key=pfc_winner_key,
            inhibited=inhibited,
            margin=margin,
            legacy_agency_score=legacy_agency_score,
        )


def config_hash_from_brain(brain: Any) -> str:
    from nexo.experiment_conditions import ExperimentCondition

    flags = getattr(brain, "experiment_flags", None)
    if flags is None:
        return ""
    cond = ExperimentCondition(
        condition_id=getattr(brain, "condition_id", "unknown"),
        condition_family=getattr(brain, "condition_family", "unknown"),
        version=1,
        description="runtime",
        parent_condition=None,
        flags=flags,
    )
    return cond.config_hash()
