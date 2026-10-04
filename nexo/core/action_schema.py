"""Generic cognitive action representation — domain-agnostic (P1)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


class ActionSchemaError(ValueError):
    """Programming error: invalid ActionSchema (not an in-world failure)."""


def _finite(name: str, value: float | None) -> float | None:
    if value is None:
        return None
    number = float(value)
    if not math.isfinite(number):
        raise ActionSchemaError(f"{name} must be finite, got {value!r}")
    return number


@dataclass(frozen=True, slots=True)
class ActionSchema:
    """What cognition may know about a candidate action.

    Identity (`id`) is stable for one decision cycle and must be a plain string
    (never `id(obj)`). Execution payloads (selectors, coordinates, handles)
    belong in the environment, not here.
    """

    id: str
    label: str
    action_type: str = "act"
    target: str | None = None
    affordance: str | None = None
    expected_effect: str | None = None
    estimated_cost: float | None = None
    risk: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not str(self.id).strip():
            raise ActionSchemaError("id must be a non-empty string")
        if not str(self.label).strip():
            raise ActionSchemaError("label must be a non-empty string")
        cost = _finite("estimated_cost", self.estimated_cost)
        risk = _finite("risk", self.risk)
        if risk is not None and not 0.0 <= risk <= 1.0:
            raise ActionSchemaError(f"risk must be in [0, 1], got {risk}")
        object.__setattr__(self, "estimated_cost", cost)
        object.__setattr__(self, "risk", risk)
        meta = self.metadata if self.metadata is not None else {}
        if isinstance(meta, MappingProxyType):
            frozen = meta
        else:
            frozen = MappingProxyType(dict(meta))
        object.__setattr__(self, "metadata", frozen)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "action_type": self.action_type,
            "target": self.target,
            "affordance": self.affordance,
            "expected_effect": self.expected_effect,
            "estimated_cost": self.estimated_cost,
            "risk": self.risk,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ActionSchema:
        return cls(
            id=str(data["id"]),
            label=str(data.get("label") or data["id"]),
            action_type=str(data.get("action_type") or "act"),
            target=None if data.get("target") is None else str(data["target"]),
            affordance=None if data.get("affordance") is None else str(data["affordance"]),
            expected_effect=(
                None if data.get("expected_effect") is None else str(data["expected_effect"])
            ),
            estimated_cost=data.get("estimated_cost"),
            risk=data.get("risk"),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass(frozen=True, slots=True)
class ActionOutcome:
    """Environment result after an apply request (domain failure ≠ crash)."""

    action_id: str
    accepted: bool
    success: bool
    reward: float
    observations: tuple[Any, ...] = ()
    error: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        reward = _finite("reward", float(self.reward))
        object.__setattr__(self, "reward", 0.0 if reward is None else reward)
        meta = self.metadata if self.metadata is not None else {}
        object.__setattr__(
            self,
            "metadata",
            meta if isinstance(meta, MappingProxyType) else MappingProxyType(dict(meta)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "accepted": self.accepted,
            "success": self.success,
            "reward": self.reward,
            "observations": list(self.observations),
            "error": self.error,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_apply_result(cls, action_id: str, payload: Mapping[str, Any]) -> ActionOutcome:
        error = payload.get("error")
        accepted = bool(payload.get("accepted", error is None))
        reward = float(payload.get("reward", 0.0) or 0.0)
        success = bool(payload.get("success", accepted and error is None))
        observations = payload.get("observations") or ()
        if isinstance(observations, list):
            observations = tuple(observations)
        meta = {k: v for k, v in payload.items() if k not in {"reward", "error", "accepted", "success", "observations"}}
        return cls(
            action_id=action_id,
            accepted=accepted,
            success=success,
            reward=reward,
            observations=tuple(observations),
            error=None if error is None else str(error),
            metadata=meta,
        )
