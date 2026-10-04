"""S14 — Debian packaging tests (user-level; no forced root persistence)."""

from __future__ import annotations

from pathlib import Path

import pytest

from services.packaging.debian.control import control_fields, package_manifest, render_control
from services.packaging.debian.layout import DebInstallLayout
from services.packaging.debian.policy import (
    DebianPackagingError,
    assert_maintainer_script_safe,
    packaging_policy,
)
from services.packaging.debian.unit import unit_is_enabled_by_default, user_unit_text
from services.packaging.debian import cli as debpack_cli

ROOT = Path(__file__).resolve().parents[1]
DEB_DIR = ROOT / "packaging" / "debian"


def test_policy_user_level_no_forced_root() -> None:
    p = packaging_policy()
    assert p["forced_root_persistence"] is False
    assert p["default_install_scope"] == "user"
    assert p["system_service_enabled_by_default"] is False
    assert p["user_systemd_unit_enabled_by_default"] is False
    assert p["enable_linger_by_default"] is False
    assert p["auto_start_on_boot"] is False
    assert "amd64" in p["architectures"]
    assert "arm64" in p["architectures_later"]


def test_stop_disable_commands() -> None:
    layout = DebInstallLayout.default_user()
    cmds = layout.stop_disable_commands()
    assert "nexo-node stop" in cmds["kill_switch"]
    assert "systemctl --user disable" in cmds["user_disable"]
    assert layout.to_dict()["forced_root"] is False


def test_maintainer_scripts_are_safe() -> None:
    for name in ("postinst", "prerm", "postrm"):
        text = (DEB_DIR / name).read_text(encoding="utf-8")
        assert_maintainer_script_safe(text)
    # Bad script must fail
    with pytest.raises(DebianPackagingError):
        assert_maintainer_script_safe("#!/bin/sh\nsystemctl enable nexo-node.service\n")
    with pytest.raises(DebianPackagingError):
        assert_maintainer_script_safe("loginctl enable-linger user\n")


def test_unit_optional_disabled_by_default() -> None:
    assert unit_is_enabled_by_default() is False
    text = user_unit_text()
    assert "[Service]" in text
    assert "ExecStop=" in text and "nexo-node stop" in text
    assert "enable this by default" in text.lower() or "NOT enable" in text or "not enabled" in text.lower() or "disabled by default" in text.lower() or "Optional" in text


def test_control_metadata() -> None:
    fields = control_fields()
    assert fields["Package"] == "nexo-node"
    assert fields["Architecture"] == "amd64"
    assert "system service" in fields["Description"].lower() or "Kill switch" in fields["Description"]
    rendered = render_control(fields)
    assert "Package: nexo-node" in rendered
    manifest = package_manifest()
    assert manifest["default_enabled_services"] == []


def test_cli_policy_and_check_scripts() -> None:
    assert debpack_cli.main(["policy"]) == 0
    assert debpack_cli.main(
        [
            "check-scripts",
            str(DEB_DIR / "postinst"),
            str(DEB_DIR / "prerm"),
            str(DEB_DIR / "postrm"),
        ]
    ) == 0


def test_packaging_files_exist() -> None:
    for name in (
        "README.md",
        "control",
        "postinst",
        "prerm",
        "postrm",
        "nexo-node.service",
        "build_deb.sh",
    ):
        assert (DEB_DIR / name).is_file()
