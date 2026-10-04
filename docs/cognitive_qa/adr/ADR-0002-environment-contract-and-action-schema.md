# ADR-0002 — Environment contract and ActionSchema

**Status:** Accepted

**Date:** 2026-08-19

**Baseline:** `integrated_v90` · P0 freeze commit `d64b70f8` · scientific `3a0233c3`

## Context

P0 showed that the integrated Cognitive Core talks to worlds through a duck type (`percepts_for_agent`, `available_actions`, `action_info`, `apply_action`), while PFC scored a frozen RoomWorld catalog (`ROOM_ACTION_SCHEMAS`: eat/rest/flee/explore/…). Cognitive QA needs the same brain to operate on other domains later (BrowserWorld in P2) without rewriting deliberation.

## Problem

- Cognition knew domain verbs by name.
- There was no explicit environment contract.
- There was no generic action representation for tracing, audit, or dynamic catalogs.
- Inventing `perceive` / `describe_action` would fork the live API.

## Decision

1. Formalize the **existing** duck type as `typing.Protocol` `EnvironmentProtocol` in `nexo/core/environment_protocol.py`. Real method names are kept.
2. Introduce immutable `ActionSchema` / `ActionOutcome` in `nexo/core/action_schema.py` as core domain types (not `nexo_qa`).
3. Move the historical RoomWorld catalog to `nexo/core/legacy_action_adapter.py`. PFC scores affordances (`consumable`, `inspectable`, …), not hardcoded verbs.
4. Prove the split with `MockWorld` (`nexo_qa/testing/mock_world.py`) bound after runtime construction. No `if mock_world` / `isinstance(RoomWorld)` in PFC.
5. Do **not** add `available_actions` to `WorldDemoFacade` in P1: v90’s 12× `explore` golden exists because the facade lacks that method and the scheduler swallows the AttributeError, so the legacy early adapter drives the hash.

## Environment contract

```text
percepts_for_agent() -> list[tuple[str, float, tuple[float, ...]]]
available_actions() -> tuple[str, ...]
action_info(action) -> {base_value, cost_energy, risk, modality}
apply_action(action) -> {reward, homeostatic_deltas, encoded_memory, ...}
optional sync_from_body(body)
optional action_schemas() -> tuple[ActionSchema, ...]
```

`action_schemas_for(world)` prefers `world.action_schemas()` when present; otherwise adapts `available_actions` + `action_info`.

## ActionSchema

Cognitive fields only: `id`, `label`, `action_type`, `target`, `affordance`, `expected_effect`, `estimated_cost`, `risk`, opaque `metadata`. Execution payloads (CSS, coordinates, handles) stay in the environment.

## Legacy compatibility strategy

RoomWorld is not rewritten. Strings remain the execution ids. `schema_from_legacy_action` / `legacy_id_from_schema` are reversible (`id` stays the verb). `ROOM_ACTION_SCHEMAS` is re-exported from deliberation for import compatibility.

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| New `perceive`/`describe_action` names | Would require changing RoomWorld and break the live scheduler. |
| Rewrite RoomWorld to ABC | High behavioral risk; P0 asked for compatibility first. |
| Browser-specific action types (`CLICK`, locators) in core | Violates domain-agnostic cognition; P2 concern. |
| `world_mode: mock` inside PFC | Core branching by world. Tests bind the world at the runtime boundary instead. |
| Add `available_actions` to WorldDemoFacade | Would let integrated BG run on v90 and **change the golden hash**. |

## Consequences

- Same Cognitive Core runs RoomWorld and MockWorld (`test_two_worlds_one_brain`).
- v90 `trajectory_hash` unchanged: `77b06e9fd77e5ca681663791fb0321e37fb63ff4d6407e68e92cf2275cce1d9c`.
- Remaining name-locks (`ROOM_ACTION_HINTS`, `GoalStack.ROOM_PLANS`, attention food/eat bonuses, metabolism verb table) stay as deferred debt.

## Known limitations

- `WorldDemoFacade` still does not implement `EnvironmentProtocol.available_actions`.
- Gate fallback still prefers `"rest"` when that candidate exists.
- `metadata` exists but core deliberation must not read environment keys (tested).

## P2 implications

BrowserWorld implements the same four methods (+ `action_schemas()`). Selectors stay inside the world. PFC must keep scoring schemas, not DOM.
