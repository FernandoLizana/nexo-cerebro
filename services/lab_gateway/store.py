"""On-disk gateway state. Experiences stay quarantined. No private keys."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any


class GatewayStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = root / "state.json"
        self.state = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {
                "nodes": {},
                "pending": {},
                "used_codes": [],
                "nonces": [],
                "jobs": [],
                "events": [],
                "experiences": [],
                "stopped": False,
                "metrics": {
                    "heartbeats": 0,
                    "jobs_accepted": 0,
                    "jobs_rejected": 0,
                    "replay_rejected": 0,
                    "bad_signatures": 0,
                },
            }
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def issue_pairing(self, *, host: str, port: int, fingerprint: str, lab_id: str, ttl_s: int = 120) -> dict[str, Any]:
        code = uuid.uuid4().hex[:8]
        payload = {
            "protocol_version": "mobile-v1",
            "host": host,
            "port": port,
            "cert_fingerprint_sha256": fingerprint,
            "pairing_code": code,
            "expires_at_ms": int(time.time() * 1000) + ttl_s * 1000,
            "lab_id": lab_id,
        }
        self.state["active_pairing"] = payload
        self.save()
        (self.root / "pairing.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    def consume_code(self, code: str, now_ms: int) -> str | None:
        active = self.state.get("active_pairing") or {}
        if code in self.state["used_codes"]:
            return "pairing code already used"
        if not active or active.get("pairing_code") != code:
            return "unknown pairing code"
        if int(active.get("expires_at_ms") or 0) < now_ms:
            return "pairing code expired"
        self.state["used_codes"].append(code)
        self.state["active_pairing"] = None
        return None

    def remember_nonce(self, nonce: str) -> bool:
        if nonce in self.state["nonces"]:
            self.state["metrics"]["replay_rejected"] += 1
            return False
        self.state["nonces"].append(nonce)
        self.state["nonces"] = self.state["nonces"][-2000:]
        return True
