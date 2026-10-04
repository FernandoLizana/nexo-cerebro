"""P1 EnvironmentProtocol, adapter, MockWorld dynamics, isolation, negatives."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from nexo.core.action_schema import ActionSchema, ActionSchemaError
from nexo.core.environment_protocol import (
    EnvironmentProtocol,
    action_schemas_for,
    apply_action_outcome,
)
from nexo.core.legacy_action_adapter import (
    legacy_id_from_schema,
    schema_from_legacy_action,
    schemas_from_action_catalog,
)
from nexo.demo.room_scenario import RoomWorld
from nexo.homeostasis.drives import DriveField
from nexo.prefrontal.deliberation import PrefrontalDeliberator
from nexo_qa.testing.mock_world import MockWorld

ROOT = Path(__file__).resolve().parent.parent


class _FakeWorld:
    def percepts_for_agent(self) -> list[tuple[str, float, tuple[float, ...]]]:
        return [("panel", 0.4, (1.0, 0.0, 0.0))]

    def available_actions(self) -> tuple[str, ...]:
        return ("press", "skip")

    def action_info(self, action: str) -> dict:
        return {"base_value": 0.3, "cost_energy": 0.01, "risk": 0.0, "modality": "panel"}

    def apply_action(self, action: str) -> dict:
        return {"reward": 0.11 if action == "press" else 0.0, "homeostatic_deltas": {}, "encoded_memory": None}


def test_fake_world_satisfies_protocol() -> None:
    world = _FakeWorld()
    assert isinstance(world, EnvironmentProtocol)
    percepts = world.percepts_for_agent()
    assert percepts[0][0] == "panel"
    schemas = action_schemas_for(world)
    assert {s.id for s in schemas} == {"press", "skip"}
    raw, outcome = apply_action_outcome(world, "press")
    assert raw["reward"] == pytest.approx(0.11)
    assert outcome.accepted is True


def test_room_world_satisfies_protocol() -> None:
    world = RoomWorld()
    assert isinstance(world, EnvironmentProtocol)
    schemas = action_schemas_for(world)
    ids = [s.id for s in schemas]
    assert ids == list(world.available_actions())
    assert "eat" in ids
    eat = next(s for s in schemas if s.id == "eat")
    assert eat.affordance == "consumable"
    assert eat.action_type == "consume"


def test_legacy_adapter_round_trip() -> None:
    info = {"base_value": 0.4, "cost_energy": 0.08, "risk": 0.05, "modality": "food"}
    schema = schema_from_legacy_action("eat", info)
    assert schema.id == "eat"
    assert schema.affordance == "consumable"
    assert schema.estimated_cost == pytest.approx(0.08)
    assert legacy_id_from_schema(schema) == "eat"
    catalog = schemas_from_action_catalog(("eat", "rest", "flee"))
    assert [s.id for s in catalog] == ["eat", "rest", "flee"]


def test_drive_bias_equivalent_for_legacy_verbs() -> None:
    drives = DriveField(drives={"hunger": 0.5, "curiosity": 0.2, "rest": 0.1, "sleep": 0.0, "social": 0.0, "safety": 0.0})
    schema = schema_from_legacy_action("eat")
    assert drives.action_bias("eat") == pytest.approx(drives.schema_bias(schema))


def test_mock_world_dynamic_actions_and_transition() -> None:
    world = MockWorld(seed=42)
    assert world.available_actions() == ("inspect_panel", "wait")
    first = world.available_actions()
    raw, outcome = apply_action_outcome(world, "inspect_panel")
    assert outcome.accepted is True
    assert raw["to_phase"] == "armed"
    second = world.available_actions()
    assert second == ("activate_switch", "step_back")
    assert first != second
    apply_action_outcome(world, "activate_switch")
    assert world.available_actions() == ("collect_target", "step_back")
    apply_action_outcome(world, "collect_target")
    assert world.phase == "done"
    assert world.available_actions() == ("finish",)


def test_mock_world_seed_reproducible() -> None:
    a = MockWorld(seed=42)
    b = MockWorld(seed=42)
    for action in ("inspect_panel", "activate_switch", "collect_target"):
        out_a, _ = apply_action_outcome(a, action)
        out_b, _ = apply_action_outcome(b, action)
        assert out_a["reward"] == out_b["reward"]
        assert a.phase == b.phase
    assert a.action_history == b.action_history


def test_unavailable_action_is_rejected_outcome() -> None:
    world = MockWorld()
    _, outcome = apply_action_outcome(world, "collect_target")
    assert outcome.accepted is False
    assert outcome.error == "action_unavailable"
    assert world.phase == "closed"


def test_duplicate_action_ids_fail() -> None:
    class DupWorld(_FakeWorld):
        def available_actions(self) -> tuple[str, ...]:
            return ("press", "press")

    with pytest.raises(ActionSchemaError, match="duplicate"):
        action_schemas_for(DupWorld())


def test_pfc_does_not_require_room_names_or_metadata_keys() -> None:
    schemas = (
        ActionSchema(id="alpha", label="alpha", affordance="consumable", expected_effect="hunger"),
        ActionSchema(
            id="beta",
            label="beta",
            affordance="inspectable",
            expected_effect="curiosity",
            metadata={"css_selector": "#forbidden", "room_coordinate": (1, 2)},
        ),
    )
    result = PrefrontalDeliberator().run(
        candidates=("alpha", "beta"),
        action_schemas=schemas,
        drives={"hunger": 0.55, "curiosity": 0.75},
        wm_items={"alpha": 0.5},
        goals=("survive",),
        plan_action=None,
        energy=0.25,
        safety_need=0.2,
        habit_bias={},
    )
    assert result.pfc_veto is True
    assert result.choice_key == "alpha"


def test_core_deliberation_does_not_import_room_or_browser() -> None:
    forbidden_names = {"RoomWorld", "BrowserWorld", "playwright", "selenium"}
    files = [
        ROOT / "nexo" / "prefrontal" / "deliberation.py",
        ROOT / "nexo" / "core" / "action_schema.py",
        ROOT / "nexo" / "core" / "environment_protocol.py",
        ROOT / "nexo_qa" / "testing" / "mock_world.py",
    ]
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
                imported.update(alias.name for alias in node.names)
        assert not (imported & forbidden_names), f"{path.name} imports {imported & forbidden_names}"
        text = path.read_text(encoding="utf-8")
        assert "playwright" not in text.lower()
        assert "selenium" not in text.lower()


def test_p1_modules_have_no_browser_imports() -> None:
    import nexo.core.action_schema as action_schema
    import nexo.core.environment_protocol as environment_protocol
    import nexo.core.legacy_action_adapter as adapter
    import nexo.prefrontal.deliberation as deliberation
    import nexo_qa.testing.mock_world as mock_world

    for module in (action_schema, environment_protocol, adapter, deliberation, mock_world):
        assert "playwright" not in module.__name__
        assert "selenium" not in module.__name__
        assert "playwright" not in dir(module)
        assert "selenium" not in dir(module)
