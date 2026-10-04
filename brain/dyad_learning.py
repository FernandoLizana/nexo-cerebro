"""Differentiated learning cycles for Nexus (active) and Nira (receptive).

Categories are explicit. Associations never auto-promote to verified facts.
Remote material stays quarantined until provenance allows promotion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Kind = Literal[
    "observation",
    "memory",
    "inference",
    "symbolic_association",
    "hypothesis",
    "verified",
]


@dataclass
class LearningRecord:
    actor: str  # nexus | nira
    kind: Kind
    content: str
    provenance: str
    validated: bool = False
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor": self.actor,
            "kind": self.kind,
            "content": self.content[:500],
            "provenance": self.provenance,
            "validated": self.validated,
            "tags": list(self.tags)[:8],
        }


def nexus_active_step(
    *,
    goal: str,
    hypothesis: str,
    observation: str,
    authorized: bool,
    evidence_ok: bool,
) -> LearningRecord:
    if not authorized:
        return LearningRecord(
            actor="nexus",
            kind="observation",
            content=f"Acción retenida (sin autorización): {goal}",
            provenance="policy",
            validated=False,
            tags=["active", "blocked"],
        )
    if evidence_ok:
        return LearningRecord(
            actor="nexus",
            kind="verified",
            content=f"Evaluado '{hypothesis}' con observación: {observation}",
            provenance="active_experiment",
            validated=True,
            tags=["active", "verified"],
        )
    return LearningRecord(
        actor="nexus",
        kind="hypothesis",
        content=f"Hipótesis pendiente '{hypothesis}': {observation}",
        provenance="active_experiment",
        validated=False,
        tags=["active", "unverified"],
    )


def nira_receptive_step(
    *,
    experience: str,
    prior_memory: str,
    authorized: bool,
) -> LearningRecord:
    if not authorized:
        return LearningRecord(
            actor="nira",
            kind="observation",
            content="Experiencia no autorizada; no se consolida.",
            provenance="policy",
            validated=False,
            tags=["receptive", "blocked"],
        )
    association = f"{experience} ↔ {prior_memory}"
    return LearningRecord(
        actor="nira",
        kind="symbolic_association",
        content=association,
        provenance="authorized_memory",
        validated=False,
        tags=["receptive", "hypothesis_candidate"],
    )


def promote_if_verified(record: LearningRecord, *, evidence_ok: bool) -> LearningRecord:
    if record.kind == "verified":
        return record
    if evidence_ok and record.kind in {"hypothesis", "symbolic_association", "inference"}:
        return LearningRecord(
            actor=record.actor,
            kind="verified",
            content=record.content,
            provenance=record.provenance + "+verification",
            validated=True,
            tags=[*record.tags, "promoted"],
        )
    return record


def quarantine_remote(content: str, *, source: str) -> LearningRecord:
    return LearningRecord(
        actor="system",
        kind="observation",
        content=content[:500],
        provenance=f"remote:{source}",
        validated=False,
        tags=["quarantine", "remote", "untrusted"],
    )
