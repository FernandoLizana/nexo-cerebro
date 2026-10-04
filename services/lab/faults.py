"""Fault injection scenarios for multi-device lab rehearsals."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from services.coordinator.auth import heartbeat_message, registration_message
from services.coordinator.service import Coordinator, CoordinatorError
from services.node.identity import load_or_create_identity


@dataclass
class FaultResult:
    name: str
    ok: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


def _register(coord: Coordinator, data_dir, name: str):
    identity, private_key = load_or_create_identity(data_dir, node_name=name)
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


def fault_bad_signature(tmp_path) -> FaultResult:
    coord = Coordinator()
    identity, _ = _register(coord, tmp_path / "n1", "n1")
    try:
        coord.heartbeat(
            node_id=identity.node_id,
            seq=1,
            ts=time.time(),
            signature=b"\x00" * 64,
        )
        return FaultResult("bad_signature", False, "bad signature was accepted")
    except CoordinatorError as exc:
        return FaultResult("bad_signature", True, str(exc))


def fault_heartbeat_timeout(tmp_path) -> FaultResult:
    coord = Coordinator(heartbeat_timeout_s=1.0)
    identity, private_key = _register(coord, tmp_path / "n1", "n1")
    t0 = 1000.0
    coord.heartbeat(
        node_id=identity.node_id,
        seq=1,
        ts=t0,
        signature=identity.sign(private_key, heartbeat_message(identity.node_id, 1, t0)),
        now=t0,
    )
    try:
        coord.dispatch_job(
            target_node_id=identity.node_id,
            job_type="RUN_NODE_SELF_CHECK",
            now=t0 + 5.0,
        )
        return FaultResult("heartbeat_timeout", False, "offline node accepted jobs")
    except CoordinatorError as exc:
        return FaultResult("heartbeat_timeout", True, str(exc))


def fault_revoke(tmp_path) -> FaultResult:
    coord = Coordinator()
    identity, private_key = _register(coord, tmp_path / "n1", "n1")
    ts = time.time()
    coord.heartbeat(
        node_id=identity.node_id,
        seq=1,
        ts=ts,
        signature=identity.sign(private_key, heartbeat_message(identity.node_id, 1, ts)),
        now=ts,
    )
    coord.revoke_node(identity.node_id)
    try:
        coord.dispatch_job(
            target_node_id=identity.node_id,
            job_type="RUN_NODE_SELF_CHECK",
            now=ts,
        )
        return FaultResult("revoke", False, "revoked node accepted jobs")
    except CoordinatorError as exc:
        return FaultResult("revoke", True, str(exc))


def fault_forbidden_job(tmp_path) -> FaultResult:
    coord = Coordinator()
    identity, private_key = _register(coord, tmp_path / "n1", "n1")
    ts = time.time()
    coord.heartbeat(
        node_id=identity.node_id,
        seq=1,
        ts=ts,
        signature=identity.sign(private_key, heartbeat_message(identity.node_id, 1, ts)),
        now=ts,
    )
    try:
        coord.dispatch_job(
            target_node_id=identity.node_id,
            job_type="EXECUTE_SHELL",
            now=ts,
        )
        return FaultResult("forbidden_job", False, "EXECUTE_SHELL was dispatched")
    except CoordinatorError as exc:
        return FaultResult("forbidden_job", True, str(exc))


DEFAULT_FAULTS: tuple[Callable, ...] = (
    fault_bad_signature,
    fault_heartbeat_timeout,
    fault_revoke,
    fault_forbidden_job,
)


def run_fault_battery(tmp_path) -> list[FaultResult]:
    return [fn(tmp_path) for fn in DEFAULT_FAULTS]
