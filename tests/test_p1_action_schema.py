"""P1 unit tests for ActionSchema / ActionOutcome."""

from __future__ import annotations

import math

import pytest

from nexo.core.action_schema import ActionOutcome, ActionSchema, ActionSchemaError


def test_valid_schema_construction() -> None:
    schema = ActionSchema(
        id="inspect_panel",
        label="inspect panel",
        action_type="inspect",
        target="panel",
        affordance="inspectable",
        expected_effect="reveal",
        estimated_cost=0.02,
        risk=0.1,
        metadata={"source": "test"},
    )
    assert schema.id == "inspect_panel"
    assert schema.risk == 0.1
    assert dict(schema.metadata) == {"source": "test"}


def test_empty_id_rejected() -> None:
    with pytest.raises(ActionSchemaError):
        ActionSchema(id="  ", label="x")


def test_empty_label_rejected() -> None:
    with pytest.raises(ActionSchemaError):
        ActionSchema(id="x", label="")


def test_nan_risk_rejected() -> None:
    with pytest.raises(ActionSchemaError):
        ActionSchema(id="x", label="x", risk=float("nan"))


def test_infinite_cost_rejected() -> None:
    with pytest.raises(ActionSchemaError):
        ActionSchema(id="x", label="x", estimated_cost=math.inf)


def test_risk_out_of_range_rejected() -> None:
    with pytest.raises(ActionSchemaError):
        ActionSchema(id="x", label="x", risk=1.5)


def test_schema_is_immutable() -> None:
    schema = ActionSchema(id="x", label="x", metadata={"a": 1})
    with pytest.raises(Exception):
        schema.id = "y"  # type: ignore[misc]
    with pytest.raises(Exception):
        schema.metadata["a"] = 2  # type: ignore[index]


def test_serialization_round_trip() -> None:
    original = ActionSchema(
        id="collect_target",
        label="collect target",
        action_type="collect",
        target="target",
        affordance="consumable",
        expected_effect="obtain",
        estimated_cost=0.03,
        risk=0.0,
        metadata={"phase": "open"},
    )
    restored = ActionSchema.from_dict(original.to_dict())
    assert restored == original
    payload = original.to_dict()
    assert "css_selector" not in payload
    assert payload["id"] == "collect_target"


def test_from_dict_missing_id() -> None:
    with pytest.raises(KeyError):
        ActionSchema.from_dict({"label": "x"})


def test_optional_cost_and_risk() -> None:
    schema = ActionSchema(id="wait", label="wait")
    assert schema.estimated_cost is None
    assert schema.risk is None


def test_action_outcome_from_apply_result() -> None:
    outcome = ActionOutcome.from_apply_result(
        "inspect_panel",
        {"reward": 0.2, "accepted": True, "success": True, "from_phase": "closed"},
    )
    assert outcome.action_id == "inspect_panel"
    assert outcome.accepted is True
    assert outcome.reward == 0.2
    assert outcome.metadata["from_phase"] == "closed"
    restored = ActionOutcome(**{**outcome.to_dict(), "observations": tuple(outcome.to_dict()["observations"])})
    assert restored.action_id == outcome.action_id


def test_rejected_action_is_data_not_crash() -> None:
    outcome = ActionOutcome.from_apply_result(
        "missing",
        {"reward": 0.0, "error": "action_unavailable", "accepted": False, "success": False},
    )
    assert outcome.accepted is False
    assert outcome.error == "action_unavailable"
