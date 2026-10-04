"""Cryptographic node identity — private key never leaves the device."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

SOFTWARE_VERSION = "0.2.0-swarm-s2"
_PRIVATE_NAME = "node_private.pem"
_PUBLIC_NAME = "node_public.pem"
_META_NAME = "node_identity.json"


@dataclass(frozen=True, slots=True)
class NodeIdentity:
    """Public identity surface for a voluntary NEXO node."""

    node_id: str
    public_key_pem: str
    node_name: str
    software_version: str
    created_at: str

    def public_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "public_key_pem": self.public_key_pem,
            "node_name": self.node_name,
            "software_version": self.software_version,
            "created_at": self.created_at,
        }

    def sign(self, private_key: Ed25519PrivateKey, message: bytes) -> bytes:
        return private_key.sign(message)

    @staticmethod
    def verify(public_key_pem: str, message: bytes, signature: bytes) -> bool:
        public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        if not isinstance(public_key, Ed25519PublicKey):
            return False
        try:
            public_key.verify(signature, message)
            return True
        except Exception:
            return False


def _node_id_from_public_pem(public_pem: str) -> str:
    digest = hashlib.sha256(public_pem.encode("utf-8")).hexdigest()
    return f"nexo-node-{digest[:32]}"


def _write_secret(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    try:
        os.chmod(path, 0o600)
    except OSError:
        # Windows may ignore POSIX mode bits; still avoid world-writable intent.
        pass


def load_or_create_identity(
    data_dir: Path | str,
    *,
    node_name: str = "local-node",
) -> tuple[NodeIdentity, Ed25519PrivateKey]:
    """Load existing keypair or create a new one under ``data_dir``.

    Returns the public ``NodeIdentity`` and the in-memory private key.
    Callers must not log or print the private key.
    """
    root = Path(data_dir)
    root.mkdir(parents=True, exist_ok=True)
    private_path = root / _PRIVATE_NAME
    public_path = root / _PUBLIC_NAME
    meta_path = root / _META_NAME

    if private_path.is_file() and public_path.is_file() and meta_path.is_file():
        private_key = serialization.load_pem_private_key(private_path.read_bytes(), password=None)
        if not isinstance(private_key, Ed25519PrivateKey):
            raise ValueError("node private key is not Ed25519")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        identity = NodeIdentity(
            node_id=str(meta["node_id"]),
            public_key_pem=public_path.read_text(encoding="utf-8"),
            node_name=str(meta.get("node_name") or node_name),
            software_version=str(meta.get("software_version") or SOFTWARE_VERSION),
            created_at=str(meta["created_at"]),
        )
        return identity, private_key

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    created_at = datetime.now(timezone.utc).isoformat()
    node_id = _node_id_from_public_pem(public_pem)
    identity = NodeIdentity(
        node_id=node_id,
        public_key_pem=public_pem,
        node_name=node_name,
        software_version=SOFTWARE_VERSION,
        created_at=created_at,
    )
    _write_secret(private_path, private_pem)
    public_path.write_text(public_pem, encoding="utf-8")
    meta_path.write_text(
        json.dumps(
            {
                "node_id": identity.node_id,
                "node_name": identity.node_name,
                "software_version": identity.software_version,
                "created_at": identity.created_at,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return identity, private_key
