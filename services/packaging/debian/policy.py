"""Hard policy rules for nexo-node.deb (S14)."""

from __future__ import annotations

from typing import Any


class DebianPackagingError(ValueError):
    pass


def packaging_policy() -> dict[str, Any]:
    """Canonical S14 policy — tests lock these values."""
    return {
        "package": "nexo-node",
        "artifact": "nexo-node.deb",
        "architectures": ["amd64"],  # arm64 later
        "architectures_later": ["arm64"],
        "forced_root_persistence": False,
        "default_install_scope": "user",
        "system_service_enabled_by_default": False,
        "user_systemd_unit_optional": True,
        "user_systemd_unit_enabled_by_default": False,
        "enable_linger_by_default": False,
        "kill_switch": "nexo-node stop",
        "disable": "systemctl --user disable --now nexo-node.service",
        "stop": "systemctl --user stop nexo-node.service  OR  nexo-node stop",
        "auto_start_on_boot": False,
        "postinst_may_systemctl_enable_system": False,
        "maintainer_scripts_must_not": [
            "systemctl enable nexo-node.service",  # system-level
            "loginctl enable-linger",
            "update-rc.d",
            "chkconfig",
        ],
    }


def assert_maintainer_script_safe(script_text: str) -> None:
    """Fail closed if maintainer scripts force root persistence."""
    policy = packaging_policy()
    lowered = script_text.lower()
    # Allow comments mentioning forbidden actions
    lines = []
    for line in script_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    body = "\n".join(lines)
    body_l = body.lower()
    for bad in policy["maintainer_scripts_must_not"]:
        if bad.lower() in body_l:
            raise DebianPackagingError(f"maintainer script contains forbidden persistence: {bad}")
    if "systemctl enable" in body_l and "--user" not in body_l:
        raise DebianPackagingError("systemctl enable without --user is forbidden by default")
    if policy["forced_root_persistence"]:
        raise DebianPackagingError("policy invariant broken: forced_root_persistence")
