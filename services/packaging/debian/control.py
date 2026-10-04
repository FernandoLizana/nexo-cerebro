"""Debian control metadata generator for nexo-node.deb."""

from __future__ import annotations

from typing import Any

from services.packaging.debian.policy import packaging_policy


def control_fields(*, version: str = "0.2.0", arch: str = "amd64") -> dict[str, str]:
    policy = packaging_policy()
    if arch not in policy["architectures"] and arch not in policy["architectures_later"]:
        raise ValueError(f"unsupported arch: {arch}")
    return {
        "Package": policy["package"],
        "Version": version,
        "Section": "science",
        "Priority": "optional",
        "Architecture": arch,
        "Depends": "python3 (>= 3.11)",
        "Maintainer": "NEXO Project <nexo@localhost>",
        "Description": (
            "NEXO Node — voluntary distributed cognitive-agent laboratory runtime\n"
            " User-level scientific node. Does not enable a system service by default.\n"
            " Kill switch: nexo-node stop. Optional systemd --user unit is disabled by default."
        ),
        "Homepage": "https://localhost/nexo",
    }


def render_control(fields: dict[str, str] | None = None) -> str:
    data = fields or control_fields()
    lines = [f"{k}: {v}" for k, v in data.items()]
    return "\n".join(lines) + "\n"


def package_manifest() -> dict[str, Any]:
    policy = packaging_policy()
    return {
        "control": control_fields(),
        "policy": policy,
        "conffiles": [],
        "default_enabled_services": [],
    }
