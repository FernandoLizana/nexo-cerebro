"""S15 — Multi-device lab tests (IDs, TLS policy, kill switch, faults)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from services.lab.experiment_id import make_experiment_id
from services.lab.killswitch import verify_kill_switch
from services.lab.session import LabError, MultiDeviceLabSession
from services.lab.tls_policy import TlsLabPolicy, TlsPolicyError

ROOT = Path(__file__).resolve().parents[1]
LAB_PKG = ROOT / "services" / "lab"
DOCS = ROOT / "docs" / "experiments"


def test_experiment_id_reproducible() -> None:
    a = make_experiment_id(lab_name="Lab", seed=7, device_ids=["b", "a"])
    b = make_experiment_id(lab_name="lab", seed=7, device_ids=["a", "b"])
    assert a == b
    c = make_experiment_id(lab_name="lab", seed=8, device_ids=["a", "b"])
    assert a != c


def test_tls_policy_rejects_plaintext_and_fl() -> None:
    TlsLabPolicy().validate()
    with pytest.raises(TlsPolicyError):
        TlsLabPolicy(allow_plaintext=True).validate()
    with pytest.raises(TlsPolicyError):
        TlsLabPolicy(allow_federated_learning=True).validate()
    with pytest.raises(TlsPolicyError):
        TlsLabPolicy(require_certificate_verification=False).validate()
    ctx = TlsLabPolicy().ssl_context()
    assert ctx.verify_mode != 0


def test_kill_switch_verified(tmp_path: Path) -> None:
    result = verify_kill_switch(tmp_path / "node", node_name="ks")
    assert result["ok"] is True
    assert result["state"] == "STOPPED"
    assert result["private_key_in_memory"] is False


def test_rehearsal_two_devices(tmp_path: Path) -> None:
    out = MultiDeviceLabSession(root=tmp_path / "lab", seed=15, lab_name="ci-lab").rehearse()
    assert out["ok"] is True
    assert out["device_count"] >= 2
    assert out["experiment_id"].startswith("exp-")
    assert out["event_quarantined"] is True
    assert out["federated_learning"] is False
    assert out["networking_enabled"] is False
    assert all(f["ok"] for f in out["faults"])
    assert len(out["kill_switches"]) >= 2
    # Same lab inputs ⇒ same experiment id
    again = make_experiment_id(
        lab_name="ci-lab",
        seed=15,
        device_ids=[d["node_id"] for d in out["devices"]],
    )
    assert again == out["experiment_id"]


def test_requires_two_devices(tmp_path: Path) -> None:
    with pytest.raises(LabError):
        MultiDeviceLabSession(root=tmp_path, min_devices=1)


def test_lab_package_no_shell_rce() -> None:
    for path in LAB_PKG.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in {"subprocess", "paramiko"}
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in {"subprocess", "paramiko"}
        assert "EXECUTE_SHELL" not in text or "forbidden" in text.lower() or "fault" in path.name


def test_runbooks_exist() -> None:
    for name in (
        "S15_MULTI_DEVICE_LAB.md",
        "S15_FAULT_INJECTION.md",
        "S15_CHECKLIST.md",
    ):
        assert (DOCS / name).is_file()
