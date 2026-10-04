"""Cross-checks for mobile-v1: signatures, jobs, pairing, quarantine, creature contract."""

from __future__ import annotations

import json
import ssl
import urllib.request
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from protocols.mobile.canonical import canonical_bytes, signed_view
from protocols.mobile.creature_tier0 import run_mobile_creature
from protocols.mobile.envelope import build_envelope
from protocols.mobile.jobs import mobile_job_allowed
from services.lab_gateway.policy import assert_explicit_private_host, flags_required
from services.lab_gateway.server import approve_node, enqueue_job, start_gateway, stop_gateway
from services.lab_gateway.store import GatewayStore
from services.node.jobs import JobRequest

ROOT = Path(__file__).resolve().parents[2]
VECTORS = Path(__file__).resolve().parent / "vectors"


def _identity():
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    return key, public.hex()


def _sign(key, message: dict) -> dict:
    signed = dict(message)
    signed["public_key_hex"] = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    ).hex()
    raw = canonical_bytes(signed_view(signed))
    signed["signature"] = key.sign(raw).hex()
    return signed


def _post(url: str, body: dict, cert_pem: bytes) -> tuple[int, dict]:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_verify_locations(cadata=cert_pem.decode("utf-8"))
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=3) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def test_flags_and_bind_policy() -> None:
    assert flags_required(False, True)
    with pytest.raises(ValueError):
        assert_explicit_private_host("0.0.0.0")
    with pytest.raises(ValueError):
        assert_explicit_private_host("8.8.8.8")
    assert assert_explicit_private_host("127.0.0.1", allow_loopback=True) == "127.0.0.1"


def test_unknown_and_forbidden_jobs() -> None:
    declared = {"RUN_CREATURE_SIMULATION", "CREATE_BEING"}
    assert mobile_job_allowed("EXECUTE_SHELL", declared)
    assert mobile_job_allowed("SCAN_NETWORK", declared)
    assert mobile_job_allowed("RUN_BROWSERWORLD_EXPERIMENT", declared)
    assert mobile_job_allowed("RUN_TEXTWORLD_EXPERIMENT", declared)
    assert mobile_job_allowed("RUN_CREATURE_SIMULATION", declared) is None
    with pytest.raises(Exception):
        JobRequest(job_type="EXECUTE_SHELL", job_id="x").validate()


def test_creature_contract_is_stable() -> None:
    a = run_mobile_creature(seed=7, ticks=5, being_id="being-1")
    b = run_mobile_creature(seed=7, ticks=5, being_id="being-1")
    assert a == b
    assert a["llm_used"] is False
    assert a["engine"] == "creature-mobile-tier0-v1"
    golden_path = VECTORS / "creature_seed7.json"
    assert golden_path.is_file(), "missing golden vector; run scripts/regen_contract_vectors.py"
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    assert a == golden


def test_python_signature_roundtrip_and_tamper() -> None:
    key, public_hex = _identity()
    message = build_envelope(
        message_type="heartbeat",
        node_id="node-test",
        payload={"seq": 1},
        timestamp_ms=1_700_000_000_000,
        nonce="n1",
        message_id="m1",
    )
    signed = _sign(key, message)
    from services.lab_gateway.verify import verify_envelope

    assert verify_envelope(signed, now_ms=1_700_000_000_000) is None
    tampered = dict(signed)
    tampered["payload"] = {"seq": 2}
    assert verify_envelope(tampered, now_ms=1_700_000_000_000) == "invalid signature"
    assert public_hex == signed["public_key_hex"]


def test_heartbeat_signed_golden_vector() -> None:
    from services.lab_gateway.verify import verify_envelope

    golden_path = VECTORS / "heartbeat_signed.json"
    assert golden_path.is_file(), "missing golden vector; run scripts/regen_contract_vectors.py"
    signed = json.loads(golden_path.read_text(encoding="utf-8"))
    assert verify_envelope(signed, now_ms=1_700_000_000_000) is None
    tampered = dict(signed)
    tampered["payload"] = {"seq": 2}
    assert verify_envelope(tampered, now_ms=1_700_000_000_000) == "invalid signature"

def test_gateway_pairing_job_quarantine_replay(tmp_path: Path) -> None:
    root = tmp_path / "gw"
    httpd = start_gateway(
        host="127.0.0.1",
        port=0,
        root=root,
        enable_mobile_lab=True,
        acknowledge_risks=True,
        allow_loopback=True,
    )
    try:
        port = httpd.server_address[1]
        store = GatewayStore(root)
        cert_pem = (root / "lab_cert.pem").read_bytes()
        pairing = store.issue_pairing(
            host="127.0.0.1",
            port=port,
            fingerprint=store.state["fingerprint"],
            lab_id="lab",
        )
        key, _public = _identity()
        node_id = "nexo-node-mobiletest"
        pair = _sign(
            key,
            build_envelope(
                message_type="pair",
                node_id=node_id,
                payload={
                    "pairing_code": pairing["pairing_code"],
                    "cert_fingerprint_sha256": pairing["cert_fingerprint_sha256"],
                    "capabilities": ["RUN_CREATURE_SIMULATION", "CREATE_BEING"],
                },
            ),
        )
        status, body = _post(f"https://127.0.0.1:{port}/v1/pair", pair, cert_pem)
        assert status == 202, body
        again, body2 = _post(f"https://127.0.0.1:{port}/v1/pair", pair, cert_pem)
        assert again in {401, 403, 409}
        assert body2["ok"] is False
        approve_node(root, node_id)
        job = enqueue_job(
            root,
            node_id,
            "RUN_CREATURE_SIMULATION",
            {"engine": "creature-mobile-tier0-v1", "seed": 7, "ticks": 3, "being_id": "b1"},
        )
        assert job["status"] == "queued"
        with pytest.raises(SystemExit):
            enqueue_job(root, node_id, "EXECUTE_SHELL", {})
        beat = _sign(
            key,
            build_envelope(message_type="heartbeat", node_id=node_id, payload={"seq": 1}),
        )
        status, body = _post(f"https://127.0.0.1:{port}/v1/heartbeat", beat, cert_pem)
        assert status == 200, body
        assert body["jobs"][0]["job_type"] == "RUN_CREATURE_SIMULATION"
        replay, replay_body = _post(f"https://127.0.0.1:{port}/v1/heartbeat", beat, cert_pem)
        assert replay == 409
        assert replay_body["error"] == "replayed nonce"
        exp = _sign(
            key,
            build_envelope(
                message_type="experience",
                node_id=node_id,
                payload={"event_type": "BEING_LEARNED", "summary": "tier0"},
            ),
        )
        status, body = _post(f"https://127.0.0.1:{port}/v1/experience", exp, cert_pem)
        assert status == 202
        assert body["status"] == "QUARANTINED"
        saved = GatewayStore(root)
        assert saved.state["experiences"][0]["status"] == "QUARANTINED"
    finally:
        stop_gateway(root)
