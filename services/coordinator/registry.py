"""Node registry + revocation."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class NodeRecord:
    node_id: str
    public_key_pem: str
    node_name: str
    software_version: str
    registered_at: float
    last_heartbeat_at: float
    heartbeat_seq: int = 0
    revoked: bool = False
    capabilities: dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "software_version": self.software_version,
            "registered_at": self.registered_at,
            "last_heartbeat_at": self.last_heartbeat_at,
            "heartbeat_seq": self.heartbeat_seq,
            "revoked": self.revoked,
            "online": False,  # filled by registry using timeout
            "capabilities": dict(self.capabilities),
            # public key is intentional for peer verification; never private key
            "public_key_pem": self.public_key_pem,
        }


class NodeRegistry:
    def __init__(self, *, heartbeat_timeout_s: float = 30.0) -> None:
        self.heartbeat_timeout_s = float(heartbeat_timeout_s)
        self._nodes: dict[str, NodeRecord] = {}

    def register(self, record: NodeRecord) -> None:
        existing = self._nodes.get(record.node_id)
        if existing and existing.revoked:
            raise ValueError(f"node revoked: {record.node_id}")
        self._nodes[record.node_id] = record

    def get(self, node_id: str) -> NodeRecord | None:
        return self._nodes.get(node_id)

    def revoke(self, node_id: str) -> None:
        node = self._nodes.get(node_id)
        if node is None:
            raise KeyError(node_id)
        node.revoked = True

    def is_active(self, node_id: str, *, now: float | None = None) -> bool:
        node = self._nodes.get(node_id)
        if node is None or node.revoked:
            return False
        now = time.time() if now is None else now
        return (now - node.last_heartbeat_at) <= self.heartbeat_timeout_s

    def list_public(self, *, now: float | None = None) -> list[dict[str, Any]]:
        now = time.time() if now is None else now
        out = []
        for node in sorted(self._nodes.values(), key=lambda n: n.node_id):
            payload = node.to_public_dict()
            payload["online"] = (not node.revoked) and (
                (now - node.last_heartbeat_at) <= self.heartbeat_timeout_s
            )
            out.append(payload)
        return out
