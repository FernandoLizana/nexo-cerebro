"""Client update payloads and poison / integrity checks."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping


class UpdateRejected(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ClientUpdate:
    node_id: str
    round_id: int
    weights: dict[str, float]
    lora_delta: dict[str, float] = field(default_factory=dict)
    signature_hex: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "round_id": self.round_id,
            "weights": dict(self.weights),
            "lora_delta": dict(self.lora_delta),
            "signature_hex": self.signature_hex,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ClientUpdate:
        return cls(
            node_id=str(data.get("node_id") or ""),
            round_id=int(data.get("round_id") or 0),
            weights={str(k): float(v) for k, v in dict(data.get("weights") or {}).items()},
            lora_delta={str(k): float(v) for k, v in dict(data.get("lora_delta") or {}).items()},
            signature_hex=None if data.get("signature_hex") is None else str(data.get("signature_hex")),
        )


def l2_norm(weights: Mapping[str, float]) -> float:
    return math.sqrt(sum(float(v) * float(v) for v in weights.values()))


def validate_client_update(
    update: ClientUpdate,
    *,
    expected_round: int,
    known_nodes: set[str],
    max_norm: float = 5.0,
    require_signature: bool = True,
) -> None:
    """Reject malicious / malformed updates (poisoning defenses — research baseline)."""
    if not update.node_id:
        raise UpdateRejected("missing node_id")
    if update.node_id not in known_nodes:
        raise UpdateRejected(f"unknown node: {update.node_id}")
    if update.round_id != expected_round:
        raise UpdateRejected(f"round mismatch: got {update.round_id} expected {expected_round}")
    if not update.weights and not update.lora_delta:
        raise UpdateRejected("empty update")
    if require_signature and not update.signature_hex:
        raise UpdateRejected("missing signature")
    if update.signature_hex is not None:
        try:
            raw = bytes.fromhex(update.signature_hex)
        except ValueError as exc:
            raise UpdateRejected("malformed signature hex") from exc
        if len(raw) < 32:
            raise UpdateRejected("signature too short")
        # Trivial poison: all-zero signature
        if raw == b"\x00" * len(raw):
            raise UpdateRejected("null signature rejected")

    for bag_name, bag in (("weights", update.weights), ("lora_delta", update.lora_delta)):
        for key, value in bag.items():
            if not math.isfinite(float(value)):
                raise UpdateRejected(f"non-finite value in {bag_name}.{key}")
            if abs(float(value)) > 10.0:
                raise UpdateRejected(f"extreme value in {bag_name}.{key}")
        norm = l2_norm(bag)
        if norm > max_norm:
            raise UpdateRejected(f"{bag_name} L2 norm {norm:.4f} exceeds max {max_norm}")
