"""Observatory read-only APIs — labels and no invented hub devices."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask

from brain.relationship_model import RelationshipModel
from nexo.observatory_api import register_observatory_routes


@pytest.fixture
def observatory_client(monkeypatch):
    """Minimal Flask app with observatory routes; hub default unreachable."""
    monkeypatch.setattr(
        "brain.collective_capacity.fetch_hub",
        lambda: {},
    )
    brain = SimpleNamespace(
        relationship_model=RelationshipModel(affinity=0.4),
        _nira_associations=[],
        _dyad_learning={},
        _nexus_dyad_log=[],
    )
    app = Flask(__name__)
    register_observatory_routes(app, brain)
    return app.test_client(), brain


def test_personalities_source_label(observatory_client) -> None:
    client, _ = observatory_client
    res = client.get("/api/personalities")
    assert res.status_code == 200
    data = res.get_json()
    assert data["source"] == "brain.personality_archetypes"
    assert data["demo"] is False
    assert "nexus" in data and "nira" in data
    assert isinstance(data.get("presets"), list)


def test_relationships_source_label(observatory_client) -> None:
    client, _ = observatory_client
    res = client.get("/api/relationships")
    assert res.status_code == 200
    data = res.get_json()
    assert data["source"] == "brain"
    assert data["available"] is True
    assert data["demo"] is False
    assert data["friendship_score"] is None
    assert data["snapshot"]["friendship_score"] is None
    assert "affinity" in data["snapshot"]


def test_autonomy_decisions_source_label(observatory_client) -> None:
    client, _ = observatory_client
    res = client.get("/api/autonomy/decisions")
    assert res.status_code == 200
    data = res.get_json()
    assert data["source"] == "brain.character_autonomy"
    assert data["demo"] is False
    assert "policy_version" in data
    assert isinstance(data.get("decisions"), list)


def test_dyad_learning_empty_source(observatory_client) -> None:
    client, _ = observatory_client
    res = client.get("/api/dyad/learning")
    assert res.status_code == 200
    data = res.get_json()
    assert data["source"] == "empty"
    assert data["available"] is False
    assert data["demo"] is False


def test_connections_hub_down_no_invented_devices(observatory_client) -> None:
    client, _ = observatory_client
    res = client.get("/api/connections/hub")
    assert res.status_code == 200
    data = res.get_json()
    assert data["available"] is False
    assert data["source"] == "unavailable"
    assert data["hub"] is None
    assert data["demo"] is False
    # Must not invent device lists when hub is down.
    assert "connections" not in data or data.get("connections") in (None, [])
    assert "devices" not in data


def test_connections_hub_up_passes_real_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        "brain.collective_capacity.fetch_hub",
        lambda: {
            "name": "lab",
            "form": "house",
            "pose": "idle",
            "mood": "calm",
            "tick": 3,
            "capacity": {"wm": 1},
            "connections": [{"id": "phone-1", "strength": 2}],
            "links": {},
            "traits": {},
        },
    )
    brain = SimpleNamespace(relationship_model=None)
    app = Flask(__name__)
    register_observatory_routes(app, brain)
    res = app.test_client().get("/api/connections/hub")
    data = res.get_json()
    assert data["available"] is True
    assert data["source"] == "presence_hub"
    assert data["hub"]["connections"][0]["id"] == "phone-1"
    assert data["demo"] is False
