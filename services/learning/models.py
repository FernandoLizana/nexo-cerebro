"""Learning artifact models (experimental; not validated cognition)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


LEARNING_FORMAT = "learning-artifact-v1"

EXPERIMENTAL_DISCLAIMER = (
    "These learning artifacts are experimental distillation products for synthetic agents. "
    "They do not constitute proven cognition, intelligence, or validated human psychology."
)


class LearningPhase(str, Enum):
    A = "A"  # baseline / control sandbox
    B = "B"  # candidate sandbox


class ArtifactStatus(str, Enum):
    SANDBOX = "SANDBOX"
    EVAL_FAILED = "EVAL_FAILED"
    EVAL_PASSED = "EVAL_PASSED"
    PROMOTED = "PROMOTED"
    ROLLED_BACK = "ROLLED_BACK"
    SUPERSEDED = "SUPERSEDED"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_artifact_id(phase: LearningPhase | str) -> str:
    p = phase.value if isinstance(phase, LearningPhase) else str(phase)
    return f"learn-{p}-{uuid.uuid4().hex[:12]}"


@dataclass
class LearningArtifact:
    artifact_id: str
    phase: LearningPhase
    weights: dict[str, float]
    metrics: dict[str, float] = field(default_factory=dict)
    status: ArtifactStatus = ArtifactStatus.SANDBOX
    parent_id: str | None = None
    source_experience_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_utc_now)
    promoted_at: str | None = None
    disclaimer: str = EXPERIMENTAL_DISCLAIMER
    format_version: str = LEARNING_FORMAT
    auto_deploy: bool = False  # always False in S16

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": self.format_version,
            "artifact_id": self.artifact_id,
            "phase": self.phase.value,
            "weights": {k: float(v) for k, v in self.weights.items()},
            "metrics": {k: float(v) for k, v in self.metrics.items()},
            "status": self.status.value,
            "parent_id": self.parent_id,
            "source_experience_ids": list(self.source_experience_ids),
            "created_at": self.created_at,
            "promoted_at": self.promoted_at,
            "disclaimer": EXPERIMENTAL_DISCLAIMER,
            "auto_deploy": False,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LearningArtifact:
        phase = LearningPhase(str(data.get("phase") or "A"))
        status_raw = str(data.get("status") or ArtifactStatus.SANDBOX.value)
        try:
            status = ArtifactStatus(status_raw)
        except ValueError:
            status = ArtifactStatus.SANDBOX
        return cls(
            artifact_id=str(data.get("artifact_id") or new_artifact_id(phase)),
            phase=phase,
            weights={str(k): float(v) for k, v in dict(data.get("weights") or {}).items()},
            metrics={str(k): float(v) for k, v in dict(data.get("metrics") or {}).items()},
            status=status,
            parent_id=None if data.get("parent_id") is None else str(data.get("parent_id")),
            source_experience_ids=[str(x) for x in list(data.get("source_experience_ids") or [])],
            created_at=str(data.get("created_at") or _utc_now()),
            promoted_at=None if data.get("promoted_at") is None else str(data.get("promoted_at")),
            disclaimer=EXPERIMENTAL_DISCLAIMER,
            auto_deploy=False,
        )
