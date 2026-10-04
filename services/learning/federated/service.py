"""Federated research service — opt-in rounds, reject poison, emit bundles."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from services.learning.federated.aggregate import aggregate_lora_deltas, apply_lora, fedavg
from services.learning.federated.bundle import build_reproducibility_bundle, write_bundle
from services.learning.federated.evaluate import evaluate_global_weights
from services.learning.federated.flags import FederatedResearchFlag, ResearchFlagError, require_research_flag
from services.learning.federated.updates import ClientUpdate, UpdateRejected, validate_client_update


class FederatedResearchError(ValueError):
    pass


class FederatedResearchService:
    """S17 sandbox. Does not touch Core. Does not auto-deploy."""

    def __init__(
        self,
        root: Path | str,
        *,
        research_flag: FederatedResearchFlag | None = None,
        seed: int = 17,
    ) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            self.flag = require_research_flag(research_flag)
        except ResearchFlagError as exc:
            raise FederatedResearchError(str(exc)) from exc
        self.seed = int(seed)
        self.known_nodes: set[str] = set()
        self.round_id = 0
        self.global_weights: dict[str, float] = {}
        self.accepted_log: list[dict[str, Any]] = []
        self.rejected_log: list[dict[str, Any]] = []

    def register_node(self, node_id: str) -> None:
        if not node_id:
            raise FederatedResearchError("node_id required")
        self.known_nodes.add(str(node_id))

    def begin_round(self) -> int:
        self.round_id += 1
        return self.round_id

    def submit_update(self, update: ClientUpdate | Mapping[str, Any]) -> dict[str, Any]:
        upd = update if isinstance(update, ClientUpdate) else ClientUpdate.from_dict(update)
        try:
            validate_client_update(
                upd,
                expected_round=self.round_id,
                known_nodes=self.known_nodes,
            )
        except UpdateRejected as exc:
            entry = {"update": upd.to_dict(), "reason": str(exc)}
            self.rejected_log.append(entry)
            return {"accepted": False, "reason": str(exc)}
        self.accepted_log.append(upd.to_dict())
        return {"accepted": True, "node_id": upd.node_id}

    def aggregate_round(
        self,
        updates: Iterable[ClientUpdate | Mapping[str, Any]] | None = None,
        *,
        holdout_claims: list[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if self.round_id < 1:
            raise FederatedResearchError("call begin_round first")
        batch: list[ClientUpdate] = []
        if updates is None:
            # Re-validate from accepted log for this round
            for raw in self.accepted_log:
                if int(raw.get("round_id") or 0) == self.round_id:
                    batch.append(ClientUpdate.from_dict(raw))
        else:
            for item in updates:
                upd = item if isinstance(item, ClientUpdate) else ClientUpdate.from_dict(item)
                result = self.submit_update(upd)
                if result.get("accepted"):
                    batch.append(upd)

        if not batch:
            raise FederatedResearchError("no accepted updates to aggregate")

        avg = fedavg(batch)
        lora = aggregate_lora_deltas(batch)
        merged = apply_lora(avg, lora)
        self.global_weights = merged
        report = evaluate_global_weights(merged, holdout_claims=holdout_claims)

        bundle = build_reproducibility_bundle(
            seed=self.seed,
            round_id=self.round_id,
            accepted=[u.to_dict() for u in batch],
            rejected=[r for r in self.rejected_log if int(r["update"].get("round_id") or 0) == self.round_id],
            global_weights=merged,
            lora_delta=lora,
            eval_report=report.to_dict(),
            research_flag=self.flag.to_dict(),
        )
        path = write_bundle(self.root / f"bundle_round_{self.round_id}.json", bundle)
        return {
            "round_id": self.round_id,
            "accepted": len(batch),
            "rejected": len([r for r in self.rejected_log if int(r["update"].get("round_id") or 0) == self.round_id]),
            "evaluation": report.to_dict(),
            "bundle_path": str(path),
            "bundle_hash": bundle["bundle_hash"],
            "auto_deploy_to_core": False,
            "core_unchanged": True,
            "global_weights": merged,
        }

    def status(self) -> dict[str, Any]:
        return {
            "research_flag": self.flag.to_dict(),
            "round_id": self.round_id,
            "known_nodes": sorted(self.known_nodes),
            "accepted": len(self.accepted_log),
            "rejected": len(self.rejected_log),
            "auto_deploy_to_core": False,
            "default_enabled": False,
        }
