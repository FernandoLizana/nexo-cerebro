"""S2 — NEXO Node runtime tests (local only, no networking)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from services.node.capability import NodeTier, build_capability_profile, infer_tier
from services.node.governor import GovernorAction, ResourceGovernor, ResourceLimits, ResourceSample
from services.node.identity import NodeIdentity, load_or_create_identity
from services.node.jobs import JobRejected, JobRequest
from services.node.runtime import NodeRuntime, NodeState

ROOT = Path(__file__).resolve().parents[1]
NODE_PKG = ROOT / "services" / "node"


def test_identity_round_trip_and_sign_verify(tmp_path: Path) -> None:
    identity, private_key = load_or_create_identity(tmp_path, node_name="lab-a")
    again, private_key_2 = load_or_create_identity(tmp_path, node_name="ignored")
    assert identity.node_id == again.node_id
    assert identity.public_key_pem == again.public_key_pem
    message = b"nexo-s2-self-check"
    signature = identity.sign(private_key, message)
    assert NodeIdentity.verify(identity.public_key_pem, message, signature) is True
    assert NodeIdentity.verify(identity.public_key_pem, b"tampered", signature) is False
    # Private key material must not appear in public_dict
    public = identity.public_dict()
    assert "private" not in json_blob(public).lower()
    assert "BEGIN PRIVATE" not in identity.public_key_pem


def json_blob(data: object) -> str:
    import json

    return json.dumps(data)


def test_governor_throttle_pause_terminate() -> None:
    gov = ResourceGovernor(
        limits=ResourceLimits(cpu_max_percent=40.0, ram_max_mb=512, max_job_seconds=10.0, gpu_enabled=False)
    )
    assert gov.evaluate(ResourceSample(cpu_percent=10.0, ram_mb=100.0)) is GovernorAction.ALLOW
    assert gov.evaluate(ResourceSample(cpu_percent=45.0, ram_mb=100.0)) is GovernorAction.THROTTLE
    assert gov.evaluate(ResourceSample(cpu_percent=60.0, ram_mb=100.0)) is GovernorAction.TERMINATE_JOB
    assert gov.evaluate(ResourceSample(cpu_percent=10.0, ram_mb=900.0)) is GovernorAction.TERMINATE_JOB
    assert gov.evaluate(ResourceSample(cpu_percent=10.0, ram_mb=10.0, job_elapsed_seconds=99)) is GovernorAction.TERMINATE_JOB
    assert gov.evaluate(ResourceSample(cpu_percent=10.0, ram_mb=10.0, gpu_requested=True)) is GovernorAction.TERMINATE_JOB
    gov.pause()
    assert gov.evaluate(ResourceSample(cpu_percent=1.0, ram_mb=1.0)) is GovernorAction.PAUSE
    gov.resume()
    assert gov.evaluate(ResourceSample(cpu_percent=1.0, ram_mb=1.0)) is GovernorAction.ALLOW


def test_job_allowlist_fail_closed() -> None:
    JobRequest(job_type="RUN_NODE_SELF_CHECK", job_id="j1").validate()
    with pytest.raises(JobRejected, match="forbidden"):
        JobRequest(job_type="EXECUTE_SHELL", job_id="j2", payload={"cmd": "whatever"}).validate()
    with pytest.raises(JobRejected, match="forbidden"):
        JobRequest(job_type="EXECUTE_SHELL_ls", job_id="j3").validate()
    with pytest.raises(JobRejected, match="not allowlisted"):
        JobRequest(job_type="RUN_ARBITRARY_PYTHON", job_id="j4").validate()


def test_runtime_start_self_check_kill_switch(tmp_path: Path) -> None:
    runtime = NodeRuntime(data_dir=tmp_path / "node", node_name="unit")
    identity = runtime.start()
    assert runtime.state is NodeState.RUNNING
    assert identity.node_id.startswith("nexo-node-")
    result = runtime.submit_job(JobRequest(job_type="RUN_NODE_SELF_CHECK", job_id="c1"))
    assert result["ok"] is True
    assert result["result"]["verified"] is True
    snapshot = runtime.kill_switch()
    assert runtime.state is NodeState.STOPPED
    assert snapshot["state"] == "STOPPED"
    assert snapshot["networking_enabled"] is False
    assert runtime._private_key is None
    # Private key file exists on disk but must not be echoed in state snapshot
    text = (tmp_path / "node" / "node_state.json").read_text(encoding="utf-8")
    assert "PRIVATE KEY" not in text
    assert (tmp_path / "node" / "node_private.pem").is_file()


def test_capability_tier_inference() -> None:
    from services.node.capability import HardwareProfile

    micro = HardwareProfile("Windows", "AMD64", 2, 1024, 10.0, False)
    assert infer_tier(micro) is NodeTier.MICRO
    profile = build_capability_profile(cpu_max_percent=25.0, battery_mode=True)
    assert profile.tier in (NodeTier.MICRO, NodeTier.LIGHT)
    assert profile.cpu_max_percent == 25.0


def test_node_package_has_no_network_or_malware_apis() -> None:
    forbidden = (
        "socket.",
        "http.client",
        "urllib.request",
        "requests.",
        "aiohttp",
        "websocket",
        "paramiko",
        "subprocess",
        "os.system",
        "keylog",
        "scapy",
    )
    for path in NODE_PKG.rglob("*.py"):
        src = path.read_text(encoding="utf-8")
        lower = src.lower()
        for token in forbidden:
            assert token.lower() not in lower, f"{path} contains forbidden token {token!r}"
        # AST: no import socket
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in {"socket", "subprocess", "requests"}
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in {"socket", "subprocess", "requests"}
