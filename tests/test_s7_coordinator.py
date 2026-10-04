"""S7 — Coordinator tests (in-process, no networking, no RCE)."""

from __future__ import annotations

import ast
import time
from pathlib import Path

import pytest

from protocols.events.codec import encode_event
from services.coordinator.auth import heartbeat_message, registration_message
from services.coordinator.service import Coordinator, CoordinatorError
from services.node.identity import load_or_create_identity

ROOT = Path(__file__).resolve().parents[1]
COORD_PKG = ROOT / "services" / "coordinator"


def _register(coord: Coordinator, tmp_path: Path, name: str = "n1"):
    identity, private_key = load_or_create_identity(tmp_path / name, node_name=name)
    challenge = coord.begin_registration(identity.node_id)
    msg = registration_message(identity.node_id, identity.node_name, challenge["nonce"])
    sig = identity.sign(private_key, msg)
    coord.register_node(
        node_id=identity.node_id,
        node_name=identity.node_name,
        public_key_pem=identity.public_key_pem,
        software_version=identity.software_version,
        signature=sig,
    )
    return identity, private_key


def test_register_heartbeat_dispatch_poll(tmp_path: Path) -> None:
    coord = Coordinator(heartbeat_timeout_s=30.0)
    identity, private_key = _register(coord, tmp_path)
    ts = time.time()
    hb = heartbeat_message(identity.node_id, 1, ts)
    coord.heartbeat(
        node_id=identity.node_id,
        seq=1,
        ts=ts,
        signature=identity.sign(private_key, hb),
        now=ts,
    )
    job = coord.dispatch_job(
        target_node_id=identity.node_id,
        job_type="RUN_NODE_SELF_CHECK",
        payload={},
        now=ts,
    )
    assert job.status == "queued"
    polled = coord.poll_jobs(identity.node_id)
    assert polled is not None
    assert polled["job_type"] == "RUN_NODE_SELF_CHECK"
    assert coord.poll_jobs(identity.node_id) is None


def test_reject_unknown_and_forbidden_jobs(tmp_path: Path) -> None:
    coord = Coordinator()
    identity, private_key = _register(coord, tmp_path)
    ts = time.time()
    coord.heartbeat(
        node_id=identity.node_id,
        seq=1,
        ts=ts,
        signature=identity.sign(private_key, heartbeat_message(identity.node_id, 1, ts)),
        now=ts,
    )
    with pytest.raises(CoordinatorError, match="not allowlisted|forbidden"):
        coord.dispatch_job(target_node_id=identity.node_id, job_type="EXECUTE_SHELL", now=ts)
    with pytest.raises(CoordinatorError, match="not allowlisted"):
        coord.dispatch_job(target_node_id=identity.node_id, job_type="RUN_ARBITRARY", now=ts)


def test_revoke_and_heartbeat_timeout(tmp_path: Path) -> None:
    coord = Coordinator(heartbeat_timeout_s=1.0)
    identity, private_key = _register(coord, tmp_path)
    t0 = 1000.0
    coord.heartbeat(
        node_id=identity.node_id,
        seq=1,
        ts=t0,
        signature=identity.sign(private_key, heartbeat_message(identity.node_id, 1, t0)),
        now=t0,
    )
    with pytest.raises(CoordinatorError, match="offline"):
        coord.dispatch_job(
            target_node_id=identity.node_id,
            job_type="RUN_NODE_SELF_CHECK",
            now=t0 + 5.0,
        )
    # Revive then revoke
    t1 = t0 + 5.0
    coord.heartbeat(
        node_id=identity.node_id,
        seq=2,
        ts=t1,
        signature=identity.sign(private_key, heartbeat_message(identity.node_id, 2, t1)),
        now=t1,
    )
    coord.revoke_node(identity.node_id)
    with pytest.raises(CoordinatorError, match="revoked"):
        coord.dispatch_job(
            target_node_id=identity.node_id,
            job_type="RUN_NODE_SELF_CHECK",
            now=t1,
        )
    with pytest.raises(CoordinatorError, match="revoked"):
        coord.heartbeat(
            node_id=identity.node_id,
            seq=3,
            ts=t1 + 1,
            signature=identity.sign(private_key, heartbeat_message(identity.node_id, 3, t1 + 1)),
            now=t1 + 1,
        )


def test_event_ingest_quarantine(tmp_path: Path) -> None:
    coord = Coordinator()
    identity, private_key = _register(coord, tmp_path)
    ts = time.time()
    coord.heartbeat(
        node_id=identity.node_id,
        seq=1,
        ts=ts,
        signature=identity.sign(private_key, heartbeat_message(identity.node_id, 1, ts)),
        now=ts,
    )
    ev = encode_event(
        event_type="WORLD_TICK",
        tick=1,
        payload={"beings": ["a"], "locations": {"a": "meadow"}},
    )
    ingested = coord.ingest_event(source_node_id=identity.node_id, event=ev)
    assert ingested["quarantined"] is True
    assert coord.status()["cognition_executed_here"] is False
    assert coord.status()["networking_enabled"] is False


def test_coordinator_has_no_shell_or_sockets() -> None:
    forbidden_imports = {"socket", "subprocess", "requests", "paramiko", "asyncio.subprocess"}
    for path in COORD_PKG.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        assert "execute_shell" not in lower or "forbidden" in lower
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in {"socket", "subprocess", "requests"}
            if isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                assert root not in {"socket", "subprocess", "requests"}
                assert node.module not in forbidden_imports
