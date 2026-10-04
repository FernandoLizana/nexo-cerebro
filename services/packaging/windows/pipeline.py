"""Signed build pipeline description — manual update channel (S13)."""

from __future__ import annotations

from typing import Any


def build_pipeline_spec() -> dict[str, Any]:
    """Document the intended Windows EXE pipeline without embedding secrets."""
    return {
        "artifact": "NEXO-Node.exe",
        "platforms": ["win10-x64", "win11-x64"],
        "builder": "pyinstaller",
        "entry": "packaging/windows/entry_nexo_node.py",
        "spec": "packaging/windows/nexo_node.spec",
        "signing": {
            "required_for_release": True,
            "tool": "signtool",
            "note": "Certificate and timestamp URL are provided by the release operator; not stored in-repo.",
        },
        "update_channel": "manual",
        "auto_update": False,
        "silent_install": False,
        "windows_service": False,
        "kill_switch": "embedded CLI: stop",
        "consent": "services.packaging.windows.consent",
    }
