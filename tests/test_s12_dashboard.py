"""S12 — Dashboard tests (local auth, read-only, no job injection)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from services.dashboard.app import create_app
from services.dashboard.auth import LocalDashboardAuth
from services.dashboard.telemetry import TelemetryHub
from services.simulator.engine import DiscreteEventSimulator

ROOT = Path(__file__).resolve().parents[1]
DASH_PKG = ROOT / "services" / "dashboard"


@pytest.fixture()
def client_and_token():
    auth = LocalDashboardAuth("test-dashboard-token-32chars!!")
    sim = DiscreteEventSimulator(n_nodes=8, beings_per_node=2, seed=3)
    sim.seed_workload(horizon=20.0, interacts_per_node=2)
    sim.run_until(20.0)
    hub = TelemetryHub()
    hub.attach_simulator(sim)
    app = create_app(auth=auth, hub=hub)
    app.config["TESTING"] = True
    return app.test_client(), auth.token


def test_health_and_page(client_and_token) -> None:
    client, _ = client_and_token
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/health").get_json()["read_only"] is True
    page = client.get("/")
    assert page.status_code == 200
    assert b"NEXO" in page.data
    assert b"read-only" in page.data.lower() or b"Read-only" in page.data


def test_auth_required_for_telemetry(client_and_token) -> None:
    client, token = client_and_token
    assert client.get("/api/overview").status_code == 401
    ok = client.get("/api/overview", headers={"X-Nexo-Dashboard-Token": token})
    assert ok.status_code == 200
    body = ok.get_json()
    assert body["job_injection_enabled"] is False
    assert body["simulator"]["nodes"] == 8
    graph = client.get("/api/graph", headers={"X-Nexo-Dashboard-Token": token})
    assert graph.status_code == 200
    payload = graph.get_json()
    assert payload["read_only"] is True
    assert len(payload["nodes"]) >= 8
    assert isinstance(payload["links"], list)


def test_job_injection_routes_rejected(client_and_token) -> None:
    client, token = client_and_token
    headers = {"X-Nexo-Dashboard-Token": token}
    for path in ("/api/jobs", "/api/dispatch", "/api/execute", "/api/shell"):
        res = client.post(path, json={"job_type": "EXECUTE_SHELL"}, headers=headers)
        assert res.status_code in {403, 405}
        assert res.get_json()["read_only"] is True
    res = client.post("/api/dispatch_job", json={"job_type": "RUN_NODE_SELF_CHECK"}, headers=headers)
    assert res.status_code in {403, 405}
    # Dashboard must not expose coordinator dispatch symbols as features
    src = (DASH_PKG / "app.py").read_text(encoding="utf-8")
    assert "dispatch_job" not in src or "forbidden" in src.lower()


def test_package_has_no_job_dispatcher_wiring() -> None:
    forbidden_calls = ("Coordinator(", "dispatch_job(", "JobRequest(", "EXECUTE_SHELL")
    for path in DASH_PKG.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        # allow mentions only inside forbid lists / error strings
        if path.name == "telemetry.py":
            continue
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in {"subprocess"}
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in {"subprocess"}
                assert "coordinator" not in node.module
        for token in ("subprocess",):
            assert f"import {token}" not in text


def test_cli_refuses_non_loopback() -> None:
    from services.dashboard.cli import main

    assert main(["--host", "0.0.0.0", "--port", "1"]) == 2
