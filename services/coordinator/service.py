"""In-process Coordinator service (S7)."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Mapping

from services.coordinator.auth import heartbeat_message, registration_message, verify_node_signature
from services.coordinator.events import EventIngestor
from services.coordinator.jobs import DispatchedJob, JobRouter
from services.coordinator.registry import NodeRecord, NodeRegistry
from services.node.jobs import JobRejected


class CoordinatorError(ValueError):
    """Coordinator rejected the request."""


@dataclass
class Coordinator:
    """Control plane: registry, heartbeats, allowlisted jobs, event ingest.

    Hard rules:
    - never executes shell / arbitrary code
    - never runs Core cognition
    - does not open network sockets in S7 (in-process only)
    """

    heartbeat_timeout_s: float = 30.0
    registry: NodeRegistry = field(init=False)
    jobs: JobRouter = field(init=False)
    events: EventIngestor = field(init=False)
    _nonces: dict[str, str] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self.registry = NodeRegistry(heartbeat_timeout_s=self.heartbeat_timeout_s)
        self.jobs = JobRouter()
        self.events = EventIngestor()

    def begin_registration(self, node_id: str) -> dict[str, str]:
        nonce = secrets.token_hex(16)
        self._nonces[node_id] = nonce
        return {"node_id": node_id, "nonce": nonce}

    def register_node(
        self,
        *,
        node_id: str,
        node_name: str,
        public_key_pem: str,
        software_version: str,
        signature: bytes,
        capabilities: Mapping[str, Any] | None = None,
        now: float | None = None,
    ) -> dict[str, Any]:
        nonce = self._nonces.get(node_id)
        if not nonce:
            raise CoordinatorError("registration nonce missing; call begin_registration first")
        message = registration_message(node_id, node_name, nonce)
        if not verify_node_signature(public_key_pem, message, signature):
            raise CoordinatorError("invalid registration signature")
        now = time.time() if now is None else now
        record = NodeRecord(
            node_id=node_id,
            public_key_pem=public_key_pem,
            node_name=node_name,
            software_version=software_version,
            registered_at=now,
            last_heartbeat_at=now,
            capabilities=dict(capabilities or {}),
        )
        try:
            self.registry.register(record)
        except ValueError as exc:
            raise CoordinatorError(str(exc)) from exc
        self._nonces.pop(node_id, None)
        return {"ok": True, "node_id": node_id, "registered": True}

    def heartbeat(
        self,
        *,
        node_id: str,
        seq: int,
        ts: float,
        signature: bytes,
        now: float | None = None,
    ) -> dict[str, Any]:
        """Client signs ``heartbeat_message(node_id, seq, ts)`` with its private key."""
        node = self.registry.get(node_id)
        if node is None:
            raise CoordinatorError("unknown node")
        if node.revoked:
            raise CoordinatorError("node revoked")
        message = heartbeat_message(node_id, seq, ts)
        if not verify_node_signature(node.public_key_pem, message, signature):
            raise CoordinatorError("invalid heartbeat signature")
        if seq <= node.heartbeat_seq:
            raise CoordinatorError("stale heartbeat seq")
        now = time.time() if now is None else now
        if abs(now - ts) > 300:
            raise CoordinatorError("heartbeat timestamp skew too large")
        node.heartbeat_seq = seq
        node.last_heartbeat_at = now
        return {"ok": True, "node_id": node_id, "online": self.registry.is_active(node_id, now=now)}

    def revoke_node(self, node_id: str) -> dict[str, Any]:
        try:
            self.registry.revoke(node_id)
        except KeyError as exc:
            raise CoordinatorError("unknown node") from exc
        return {"ok": True, "node_id": node_id, "revoked": True}

    def dispatch_job(
        self,
        *,
        target_node_id: str,
        job_type: str,
        payload: Mapping[str, Any] | None = None,
        now: float | None = None,
    ) -> DispatchedJob:
        node = self.registry.get(target_node_id)
        if node is None:
            raise CoordinatorError("unknown node")
        if node.revoked:
            raise CoordinatorError("node revoked")
        if not self.registry.is_active(target_node_id, now=now):
            raise CoordinatorError("node offline / heartbeat timeout")
        try:
            return self.jobs.enqueue(
                target_node_id=target_node_id,
                job_type=job_type,
                payload=payload,
            )
        except JobRejected as exc:
            raise CoordinatorError(str(exc)) from exc

    def poll_jobs(self, node_id: str) -> dict[str, Any] | None:
        node = self.registry.get(node_id)
        if node is None or node.revoked:
            raise CoordinatorError("node not authorized")
        job = self.jobs.poll(node_id)
        return None if job is None else job.to_dict()

    def ingest_event(self, *, source_node_id: str, event: Mapping[str, Any]) -> dict[str, Any]:
        node = self.registry.get(source_node_id)
        if node is None or node.revoked:
            raise CoordinatorError("node not authorized")
        if not self.registry.is_active(source_node_id):
            raise CoordinatorError("node offline / heartbeat timeout")
        item = self.events.ingest(source_node_id=source_node_id, event=event)
        return item.to_dict()

    def status(self) -> dict[str, Any]:
        return {
            "networking_enabled": False,
            "heartbeat_timeout_s": self.heartbeat_timeout_s,
            "nodes": self.registry.list_public(),
            "quarantine_events": len(self.events.list_quarantine(limit=10_000)),
            "cognition_executed_here": False,
        }
