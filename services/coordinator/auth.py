"""Coordinator auth — verify node signatures; never hold private keys."""

from __future__ import annotations

from services.node.identity import NodeIdentity


def verify_node_signature(public_key_pem: str, message: bytes, signature: bytes) -> bool:
    return NodeIdentity.verify(public_key_pem, message, signature)


def registration_message(node_id: str, node_name: str, nonce: str) -> bytes:
    return f"nexo-register|{node_id}|{node_name}|{nonce}".encode("utf-8")


def heartbeat_message(node_id: str, seq: int, ts: float) -> bytes:
    return f"nexo-heartbeat|{node_id}|{seq}|{ts:.6f}".encode("utf-8")
