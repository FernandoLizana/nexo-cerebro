"""Security and personality regressions for the NEXO hardening pass."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
import zipfile

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from brain.dyad_learning import nira_receptive_step, nexus_active_step, promote_if_verified
from brain.personality_archetypes import all_presets, decide, get_preset
from nexo_qa.browser.policy import BrowserPolicy
from protocols.mobile.canonical import canonical_bytes, signed_view
from protocols.mobile.envelope import build_envelope
from scripts.build_release_artifact import scan_artifact_for_secrets
from services.being.store import BeingStore
from services.being.validation import BeingValidationError
from services.lab_gateway.verify import verify_envelope
from services.memory.local.models import MemoryKind
from services.memory.local.recall import MemoryPolicyError
from services.memory.local.store import LocalMemoryStore


def test_browser_policy_rejects_prefix_spoofs() -> None:
    policy = BrowserPolicy()
    assert policy.is_allowed_url("http://127.0.0.1:8765/x")
    assert policy.is_allowed_url("http://localhost:3000/")
    assert not policy.is_allowed_url("http://localhost.attacker.invalid/")
    assert not policy.is_allowed_url("http://127.0.0.1.attacker.invalid/")
    assert not policy.is_allowed_url("http://localhost@attacker.invalid/")
    assert not policy.is_allowed_url("file:///etc/passwd")


def test_verify_rejects_foreign_registered_key() -> None:
    key = Ed25519PrivateKey.generate()
    other = Ed25519PrivateKey.generate()
    msg = build_envelope(
        message_type="heartbeat",
        node_id="node-aaaaaaaa",
        payload={},
        nonce="n" * 32,
        timestamp_ms=1_700_000_000_000,
    )
    msg["public_key_hex"] = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    ).hex()
    msg["signature"] = key.sign(canonical_bytes(signed_view(msg))).hex()
    foreign = other.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    ).hex()
    assert verify_envelope(msg, now_ms=1_700_000_000_000, expected_public_key_hex=foreign) == (
        "public key does not match registered node"
    )
    assert (
        verify_envelope(
            msg,
            now_ms=1_700_000_000_000,
            expected_public_key_hex=msg["public_key_hex"],
        )
        is None
    )


def test_being_store_rejects_path_escape(tmp_path) -> None:
    store = BeingStore(tmp_path / "beings")
    with pytest.raises(BeingValidationError):
        store.paths_for("../escape")
    with pytest.raises(BeingValidationError):
        store.paths_for("a/b")
    with pytest.raises(BeingValidationError):
        store.paths_for("..\\windows")


def test_presence_auth_allows_emulator_lab_host() -> None:
    from services.presence.auth import host_is_loopback, origin_is_loopback_or_absent

    assert host_is_loopback("10.0.2.2:8770")
    assert host_is_loopback("127.0.0.1:8770")
    assert not host_is_loopback("evil.example")
    assert origin_is_loopback_or_absent(None)
    assert origin_is_loopback_or_absent("http://10.0.2.2:8770")
    assert not origin_is_loopback_or_absent("http://evil.example")


def test_local_memory_rejects_path_escape(tmp_path) -> None:
    beings = tmp_path / "beings"
    BeingStore(beings)
    with pytest.raises(BeingValidationError):
        LocalMemoryStore.for_being(beings, "../escape")
    with pytest.raises(BeingValidationError):
        LocalMemoryStore.for_being(beings, "a/b")
    mem = LocalMemoryStore(tmp_path / "mem", being_id="b1")
    with pytest.raises(MemoryPolicyError):
        mem._path_for(MemoryKind.EPISODIC, "../evil")
    with pytest.raises(MemoryPolicyError):
        mem._path_for(MemoryKind.EPISODIC, "a/b")


def test_twelve_archetype_presets_and_decision_divergence() -> None:
    presets = all_presets()
    assert len(presets) == 12
    assert get_preset("sage") is not None
    assert get_preset("virgo") is None
    a = decide(archetype="hero", proposal="explorar", trust=0.5, seed=7)
    v = decide(archetype="sage", proposal="explorar", trust=0.5, seed=7)
    assert a["choice"] in {"accept", "reject", "negotiate", "postpone", "ask_info", "rest"}
    assert v["policy_version"] == "jung-archetype-autonomy-v1"
    assert a["options"] != v["options"]


def test_nexus_nira_learning_categories() -> None:
    active = nexus_active_step(
        goal="medir",
        hypothesis="x sube",
        observation="x no subió",
        authorized=True,
        evidence_ok=False,
    )
    assert active.kind == "hypothesis" and not active.validated
    verified = nexus_active_step(
        goal="medir",
        hypothesis="x sube",
        observation="x subió",
        authorized=True,
        evidence_ok=True,
    )
    assert verified.kind == "verified" and verified.validated
    assoc = nira_receptive_step(
        experience="lluvia en la casa",
        prior_memory="frío en la ventana",
        authorized=True,
    )
    assert assoc.kind == "symbolic_association" and not assoc.validated
    still = promote_if_verified(assoc, evidence_ok=False)
    assert still.kind == "symbolic_association"
    promoted = promote_if_verified(assoc, evidence_ok=True)
    assert promoted.kind == "verified" and promoted.validated


def test_presence_hub_rejects_unauthorized_mutation(monkeypatch) -> None:
    monkeypatch.setenv("NEXO_PRESENCE_TOKEN", "presence-hardening-token!!")
    from services.presence.hub import presence_auth, reset_presence_auth, serve, snapshot

    reset_presence_auth()
    before_tick = snapshot()["tick"]
    httpd = serve(port=0)
    port = httpd.server_address[1]
    body = json.dumps({"source": "local", "kind": "TEACH", "text": "no debe entrar"}).encode()
    try:
        bad = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/interact",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            urllib.request.urlopen(bad, timeout=3)
        assert excinfo.value.code == 401
        assert snapshot()["tick"] == before_tick

        spoof = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/interact",
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Nexo-Presence-Token": presence_auth().token,
                "Origin": "http://evil.example",
            },
        )
        with pytest.raises(urllib.error.HTTPError) as spoof_exc:
            urllib.request.urlopen(spoof, timeout=3)
        assert spoof_exc.value.code == 403
        assert snapshot()["tick"] == before_tick
    finally:
        httpd.shutdown()
        reset_presence_auth()


def test_scan_artifact_for_secrets_fails_closed(tmp_path) -> None:
    clean = tmp_path / "clean.zip"
    dirty = tmp_path / "dirty.zip"
    with zipfile.ZipFile(clean, "w") as zf:
        zf.writestr("README.md", "# ok\n")
    with zipfile.ZipFile(dirty, "w") as zf:
        zf.writestr("configs/app.yaml", "mode: lab\n")
        zf.writestr("data/nexo_dashboard/dashboard_token.txt", "leak\n")
        zf.writestr("secrets/id_ed25519", "PRIVATE\n")
    with zipfile.ZipFile(clean, "r") as zf:
        assert scan_artifact_for_secrets(zf) == []
    with zipfile.ZipFile(dirty, "r") as zf:
        hits = scan_artifact_for_secrets(zf)
    assert any("dashboard_token" in h for h in hits)
    assert any("id_ed25519" in h for h in hits)
