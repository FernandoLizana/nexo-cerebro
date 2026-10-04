"""Structural environment contract matching the live RoomWorld duck type (P1)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from nexo.core.action_schema import ActionOutcome, ActionSchema, ActionSchemaError
from nexo.core.legacy_action_adapter import schemas_from_action_catalog


@runtime_checkable
class EnvironmentProtocol(Protocol):
    """Minimal agent↔world surface already used by the integrated scheduler.

    Real method names (do not invent perceive/describe_action):
    `percepts_for_agent`, `available_actions`, `action_info`, `apply_action`.
    Optional: `sync_from_body`.
    """

    def percepts_for_agent(self) -> list[tuple[str, float, tuple[float, ...]]]:
        ...

    def available_actions(self) -> tuple[str, ...]:
        ...

    def action_info(self, action: str) -> dict[str, Any]:
        ...

    def apply_action(self, action: str) -> dict[str, Any]:
        ...


def _assert_unique_schema_ids(schemas: tuple[ActionSchema, ...]) -> None:
    seen: set[str] = set()
    for schema in schemas:
        if schema.id in seen:
            raise ActionSchemaError(f"duplicate action id in catalog: {schema.id!r}")
        seen.add(schema.id)


def action_schemas_for(world: Any) -> tuple[ActionSchema, ...]:
    """Build ActionSchemas from a duck-typed world without isinstance checks.

    If the world exposes `action_schemas()`, that catalog is used (MockWorld).
    Otherwise schemas are adapted from `available_actions()` + `action_info()`.
    """
    provider = getattr(world, "action_schemas", None)
    if callable(provider):
        schemas = tuple(provider())
        _assert_unique_schema_ids(schemas)
        return schemas
    actions = tuple(world.available_actions())
    infos = {action: dict(world.action_info(action) or {}) for action in actions}
    schemas = schemas_from_action_catalog(actions, infos)
    _assert_unique_schema_ids(schemas)
    return schemas


def apply_action_outcome(world: Any, action_id: str) -> tuple[dict[str, Any], ActionOutcome]:
    raw = world.apply_action(action_id)
    payload = dict(raw or {})
    return payload, ActionOutcome.from_apply_result(action_id, payload)
