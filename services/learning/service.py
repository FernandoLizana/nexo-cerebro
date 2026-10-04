"""Collective learning facade — distill A/B, eval, manual promote, rollback."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from services.learning.eval_gates import compare_phases, evaluate_artifact
from services.learning.models import ArtifactStatus, LearningArtifact, LearningPhase
from services.learning.registry import ArtifactRegistry, RegistryError
from services.learning.sandbox import distill_from_claims


class CollectiveLearningError(ValueError):
    pass


class CollectiveLearningService:
    """Phase A/B sandboxes with explicit promote and rollback.

    Hard rules:
    - never auto-deploy weights
    - promote is manual and requires eval gates
    - rollback restores the previous promoted artifact
    """

    def __init__(self, root: Path | str) -> None:
        self.registry = ArtifactRegistry(root)
        self._previous_active_id: str | None = None

    def distill(
        self,
        *,
        phase: LearningPhase | str,
        claims: Iterable[Mapping[str, Any]],
        base: LearningArtifact | None = None,
        experience_ids: list[str] | None = None,
    ) -> LearningArtifact:
        phase_e = phase if isinstance(phase, LearningPhase) else LearningPhase(str(phase))
        artifact = distill_from_claims(
            phase=phase_e,
            claims=claims,
            base_weights=None if base is None else base.weights,
            parent_id=None if base is None else base.artifact_id,
            experience_ids=experience_ids,
        )
        self.registry.save(artifact)
        return artifact

    def run_ab(
        self,
        *,
        claims: Iterable[Mapping[str, Any]],
        experience_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        claims_list = list(claims)
        active = self.registry.get_active()
        a = self.distill(phase=LearningPhase.A, claims=claims_list, base=active, experience_ids=experience_ids)
        b = self.distill(phase=LearningPhase.B, claims=claims_list, base=active, experience_ids=experience_ids)
        cmp = compare_phases(a, b)
        return {
            "phase_a": a.to_dict(),
            "phase_b": b.to_dict(),
            "comparison": cmp,
            "auto_deploy": False,
            "manual_promote_only": True,
        }

    def evaluate(self, artifact_id: str) -> dict[str, Any]:
        try:
            artifact = self.registry.load(artifact_id)
        except RegistryError as exc:
            raise CollectiveLearningError(str(exc)) from exc
        baseline = self.registry.get_active()
        result = evaluate_artifact(artifact, baseline=baseline)
        artifact.status = ArtifactStatus.EVAL_PASSED if result.passed else ArtifactStatus.EVAL_FAILED
        self.registry.save(artifact)
        return {"artifact_id": artifact_id, "status": artifact.status.value, **result.to_dict()}

    def promote(self, artifact_id: str, *, allow_auto: bool = False) -> LearningArtifact:
        if allow_auto:
            raise CollectiveLearningError("auto promote is forbidden in S16 (manual only)")
        try:
            artifact = self.registry.load(artifact_id)
        except RegistryError as exc:
            raise CollectiveLearningError(str(exc)) from exc
        if artifact.status is not ArtifactStatus.EVAL_PASSED:
            # Allow evaluate-then-promote in one call path only if gates pass now
            baseline = self.registry.get_active()
            gate = evaluate_artifact(artifact, baseline=baseline)
            if not gate.passed:
                artifact.status = ArtifactStatus.EVAL_FAILED
                self.registry.save(artifact)
                raise CollectiveLearningError(f"eval gates failed: {list(gate.reasons)}")
            artifact.status = ArtifactStatus.EVAL_PASSED

        current = self.registry.get_active()
        if current is not None:
            self._previous_active_id = current.artifact_id
            current.status = ArtifactStatus.SUPERSEDED
            self.registry.save(current)

        artifact.status = ArtifactStatus.PROMOTED
        artifact.promoted_at = datetime.now(timezone.utc).isoformat()
        artifact.auto_deploy = False
        self.registry.save(artifact)
        self.registry.set_active(artifact)
        self.registry._append_history(  # noqa: SLF001
            {
                "action": "promote",
                "artifact_id": artifact.artifact_id,
                "previous": self._previous_active_id,
                "manual": True,
            }
        )
        return artifact

    def rollback(self) -> LearningArtifact:
        """Restore previously promoted artifact; clear active if none."""
        if not self._previous_active_id:
            # Try recover from history
            for event in reversed(self.registry.history()):
                if event.get("action") == "promote" and event.get("previous"):
                    self._previous_active_id = str(event["previous"])
                    break
        if not self._previous_active_id:
            raise CollectiveLearningError("no previous promoted artifact to restore")
        try:
            prior = self.registry.load(self._previous_active_id)
        except RegistryError as exc:
            raise CollectiveLearningError(str(exc)) from exc

        current = self.registry.get_active()
        if current is not None:
            current.status = ArtifactStatus.ROLLED_BACK
            self.registry.save(current)

        prior.status = ArtifactStatus.PROMOTED
        prior.promoted_at = datetime.now(timezone.utc).isoformat()
        self.registry.save(prior)
        self.registry.set_active(prior)
        self.registry._append_history(  # noqa: SLF001
            {"action": "rollback", "artifact_id": prior.artifact_id, "from": None if current is None else current.artifact_id}
        )
        # After rollback, previous becomes the rolled-back current id for possible re-rollback chains
        self._previous_active_id = None if current is None else current.artifact_id
        return prior

    def status(self) -> dict[str, Any]:
        active = self.registry.get_active()
        return {
            "auto_deploy": False,
            "manual_promote_only": True,
            "federated_learning": False,
            "active": None if active is None else active.to_dict(),
            "history_events": len(self.registry.history()),
            "disclaimer": active.disclaimer if active else None,
        }
