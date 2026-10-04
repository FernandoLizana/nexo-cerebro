"""S13 — Windows packaging tests (consent, no silent install, clean uninstall)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.packaging.windows.consent import (
    CONSENT_STATEMENTS,
    ConsentError,
    ensure_consent_file,
    require_consent,
    write_consent,
)
from services.packaging.windows.layout import (
    FORBIDDEN_SERVICE_NAMES,
    InstallLayout,
    simulate_uninstall,
    uninstall_plan,
    write_uninstall_manifest,
)
from services.packaging.windows.pipeline import build_pipeline_spec
from services.packaging.windows.silent_policy import SilentInstallError, reject_silent_flags
from services.packaging.windows import cli as winpack_cli


def test_consent_required_and_persisted(tmp_path: Path) -> None:
    with pytest.raises(ConsentError):
        require_consent(accept_all=False)
    with pytest.raises(ConsentError):
        require_consent(accept_all=False, accept_flags=[True] * (len(CONSENT_STATEMENTS) - 1) + [False])
    record = require_consent(accept_all=True)
    assert record.accepted is True
    path = write_consent(tmp_path / "consent.json", record)
    assert ensure_consent_file(path).accepted is True
    with pytest.raises(ConsentError):
        ensure_consent_file(tmp_path / "missing.json")


def test_silent_flags_rejected() -> None:
    for flag in ("/S", "/silent", "/quiet", "--silent", "/VERYSILENT", "/qn"):
        with pytest.raises(SilentInstallError):
            reject_silent_flags(["accept-consent", flag])
    reject_silent_flags(["accept-consent", "--i-accept-all"])  # ok


def test_uninstall_plan_has_no_services_and_cleans(tmp_path: Path) -> None:
    layout = InstallLayout(install_root=tmp_path / "NEXO" / "Node", data_root=tmp_path / "NEXO" / "Node" / "data")
    layout.install_root.mkdir(parents=True)
    layout.data_root.mkdir(parents=True)
    (layout.install_root / "NEXO-Node.exe").write_text("stub", encoding="utf-8")
    write_consent(layout.consent_path, require_consent(accept_all=True))
    write_uninstall_manifest(layout)
    plan = uninstall_plan(layout)
    assert plan["remove_windows_services"] == []
    assert set(plan["verify_no_services"]) == set(FORBIDDEN_SERVICE_NAMES)
    assert plan["kill_switch_before_uninstall"] is True

    dry = simulate_uninstall(layout, dry_run=True)
    assert dry["dry_run"] is True
    assert layout.consent_path.is_file()

    done = simulate_uninstall(layout, dry_run=False)
    assert done["clean"] is True
    assert done["services_registered"] == []
    assert not layout.install_root.exists()


def test_pipeline_is_manual_and_not_silent() -> None:
    spec = build_pipeline_spec()
    assert spec["artifact"] == "NEXO-Node.exe"
    assert spec["silent_install"] is False
    assert spec["auto_update"] is False
    assert spec["windows_service"] is False
    assert spec["update_channel"] == "manual"
    assert spec["signing"]["required_for_release"] is True


def test_cli_rejects_silent_and_accepts_consent(tmp_path: Path) -> None:
    assert winpack_cli.main(["/S", "accept-consent", "--i-accept-all"]) == 2
    root = tmp_path / "inst"
    assert winpack_cli.main(["accept-consent", "--i-accept-all", "--install-root", str(root)]) == 0
    assert (root / "consent.json").is_file()
    manifest = json.loads((root / "uninstall.json").read_text(encoding="utf-8"))
    assert manifest["plan"]["remove_windows_services"] == []


def test_startup_entry_forbidden(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="forbids"):
        InstallLayout(
            install_root=tmp_path,
            data_root=tmp_path / "data",
            create_startup_entry=True,
        )


def test_packaging_scripts_exist() -> None:
    root = Path(__file__).resolve().parents[1] / "packaging" / "windows"
    for name in ("README.md", "build_exe.ps1", "uninstall.ps1", "nexo_node.spec", "entry_nexo_node.py"):
        assert (root / name).is_file()
