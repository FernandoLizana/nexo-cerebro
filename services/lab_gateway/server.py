"""Opt-in TLS gateway. Does not turn the S7 coordinator into a socket server."""

from __future__ import annotations

import json
import ssl
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from protocols.mobile import MAX_MESSAGE_BYTES
from protocols.mobile.jobs import mobile_job_allowed
from services.lab_gateway.certs import load_or_create_lab_cert
from services.lab_gateway.policy import assert_explicit_private_host, flags_required
from services.lab_gateway.store import GatewayStore
from services.lab_gateway.verify import verify_envelope

_ACTIVE: dict[str, Any] = {}


class _Handler(BaseHTTPRequestHandler):
    store: GatewayStore
    fingerprint: str
    lab_id: str

    def log_message(self, fmt: str, *args: Any) -> None:
        # Do not log request lines (they can contain pairing codes).
        return

    def _json(self, code: int, body: dict[str, Any]) -> None:
        raw = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read(self) -> dict[str, Any] | None:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_MESSAGE_BYTES:
            self._json(413, {"ok": False, "error": "message too large"})
            return None
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            self._json(400, {"ok": False, "error": "invalid json"})
            return None
        if not isinstance(data, dict):
            self._json(400, {"ok": False, "error": "object required"})
            return None
        return data

    def do_POST(self) -> None:  # noqa: N802
        self.store.state = self.store._load()
        if self.store.state.get("stopped"):
            self._json(503, {"ok": False, "error": "gateway stopped"})
            return
        message = self._read()
        if message is None:
            return
        now = int(time.time() * 1000)
        if self.path == "/v1/pair":
            self._pair(message, now)
            return
        node_id = str(message.get("node_id") or "")
        registered = self.store.state["nodes"].get(node_id)
        if not registered or registered.get("status") != "approved":
            self._json(403, {"ok": False, "error": "node not approved"})
            return
        error = verify_envelope(
            message,
            now_ms=now,
            expected_public_key_hex=str(registered.get("public_key_hex") or ""),
        )
        if error:
            self.store.state["metrics"]["bad_signatures"] += 1
            self.store.save()
            self._json(401, {"ok": False, "error": error})
            return
        if not self.store.remember_nonce(str(message["nonce"])):
            self.store.save()
            self._json(409, {"ok": False, "error": "replayed nonce"})
            return
        node = registered
        if self.path == "/v1/heartbeat":
            self.store.state["metrics"]["heartbeats"] += 1
            node["last_heartbeat_ms"] = now
            self.store.save()
            self._json(200, {"ok": True, "jobs": _jobs_for(self.store, message["node_id"])})
            return
        if self.path == "/v1/experience":
            self.store.state["experiences"].append(
                {
                    "node_id": message["node_id"],
                    "status": "QUARANTINED",
                    "received_ms": now,
                    "payload": message["payload"],
                }
            )
            self.store.save()
            self._json(202, {"ok": True, "status": "QUARANTINED"})
            return
        if self.path == "/v1/events":
            self.store.state["events"].append(
                {"node_id": message["node_id"], "received_ms": now, "payload": message["payload"]}
            )
            self.store.save()
            self._json(202, {"ok": True, "quarantined": True})
            return
        self._json(404, {"ok": False, "error": "unknown route"})

    def _pair(self, message: dict[str, Any], now: int) -> None:
        error = verify_envelope(message, now_ms=now)
        if error:
            self.store.state["metrics"]["bad_signatures"] += 1
            self.store.save()
            self._json(401, {"ok": False, "error": error})
            return
        if not self.store.remember_nonce(str(message["nonce"])):
            self.store.save()
            self._json(409, {"ok": False, "error": "replayed nonce"})
            return
        payload = message.get("payload") if isinstance(message.get("payload"), dict) else {}
        code = str(payload.get("pairing_code") or "")
        fingerprint = str(payload.get("cert_fingerprint_sha256") or "")
        error = self.store.consume_code(code, now)
        if error:
            self._json(403, {"ok": False, "error": error})
            self.store.save()
            return
        if fingerprint != self.fingerprint:
            self._json(403, {"ok": False, "error": "certificate fingerprint mismatch"})
            self.store.save()
            return
        node_id = str(message.get("node_id") or "")
        public_key_hex = str(message.get("public_key_hex") or "")
        if len(node_id) < 8 or len(public_key_hex) != 64:
            self._json(400, {"ok": False, "error": "invalid identity"})
            self.store.save()
            return
        declared = payload.get("capabilities") or []
        if not isinstance(declared, list):
            declared = []
        self.store.state["pending"][node_id] = {
            "node_id": node_id,
            "public_key_hex": public_key_hex,
            "capabilities": [str(x) for x in declared],
            "requested_ms": now,
            "lab_id": self.lab_id,
        }
        self.store.save()
        self._json(202, {"ok": True, "status": "pending_pc_approval", "node_id": node_id})


def _jobs_for(store: GatewayStore, node_id: str) -> list[dict[str, Any]]:
    ready = [job for job in store.state["jobs"] if job.get("target") == node_id and job.get("status") == "queued"]
    for job in ready:
        job["status"] = "delivered"
    return ready


def approve_node(root: Path, node_id: str) -> dict[str, Any]:
    store = GatewayStore(root)
    pending = store.state["pending"].pop(node_id, None)
    if not pending:
        raise SystemExit(f"no pending pairing for {node_id}")
    pending["status"] = "approved"
    store.state["nodes"][node_id] = pending
    store.save()
    return pending


def enqueue_job(root: Path, node_id: str, job_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    store = GatewayStore(root)
    node = store.state["nodes"].get(node_id)
    if not node or node.get("status") != "approved":
        raise SystemExit("node not approved")
    error = mobile_job_allowed(job_type, set(node.get("capabilities") or []))
    if error:
        store.state["metrics"]["jobs_rejected"] += 1
        store.save()
        raise SystemExit(error)
    job = {
        "job_id": f"job-{int(time.time())}",
        "job_type": job_type,
        "target": node_id,
        "payload": payload,
        "status": "queued",
    }
    store.state["jobs"].append(job)
    store.state["metrics"]["jobs_accepted"] += 1
    store.save()
    return job


def start_gateway(
    *,
    host: str,
    port: int,
    root: Path,
    enable_mobile_lab: bool,
    acknowledge_risks: bool,
    allow_loopback: bool = False,
    lab_id: str = "local-lab",
) -> ThreadingHTTPServer:
    refused = flags_required(enable_mobile_lab, acknowledge_risks)
    if refused:
        raise SystemExit(refused)
    host = assert_explicit_private_host(host, allow_loopback=allow_loopback)
    root.mkdir(parents=True, exist_ok=True)
    cert, key, fingerprint = load_or_create_lab_cert(root, host=host)
    store = GatewayStore(root)
    store.state["stopped"] = False
    store.state["fingerprint"] = fingerprint
    store.save()

    handler = type(
        "BoundHandler",
        (_Handler,),
        {"store": store, "fingerprint": fingerprint, "lab_id": lab_id},
    )
    httpd = ThreadingHTTPServer((host, port), handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(certfile=str(cert), keyfile=str(key))
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    thread = threading.Thread(target=httpd.serve_forever, name="nexo-lab-gateway", daemon=True)
    thread.start()
    _ACTIVE["httpd"] = httpd
    _ACTIVE["thread"] = thread
    _ACTIVE["root"] = root
    return httpd


def stop_gateway(root: Path | None = None) -> None:
    httpd = _ACTIVE.get("httpd")
    if httpd is not None:
        httpd.shutdown()
        httpd.server_close()
        _ACTIVE.clear()
    if root is not None:
        store = GatewayStore(root)
        store.state["stopped"] = True
        store.save()
