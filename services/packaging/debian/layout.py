"""User-local install layout for Debian packaging (S14)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class DebInstallLayout:
    """Prefer user-writable paths; system paths are optional and non-default."""

    prefix: Path
    data_root: Path
    unit_dir: Path
    scope: str = "user"  # user | system

    def __post_init__(self) -> None:
        if self.scope not in {"user", "system"}:
            raise ValueError("scope must be user|system")
        if self.scope == "system":
            # Allowed to describe, but packaging_policy forbids enabling by default.
            pass

    @classmethod
    def default_user(cls) -> DebInstallLayout:
        home = Path.home()
        xdg_data = Path(os.environ.get("XDG_DATA_HOME") or (home / ".local" / "share"))
        xdg_config = Path(os.environ.get("XDG_CONFIG_HOME") or (home / ".config"))
        return cls(
            prefix=home / ".local",
            data_root=xdg_data / "nexo" / "node",
            unit_dir=xdg_config / "systemd" / "user",
            scope="user",
        )

    @property
    def bin_path(self) -> Path:
        return self.prefix / "bin" / "nexo-node"

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope": self.scope,
            "prefix": str(self.prefix),
            "bin": str(self.bin_path),
            "data_root": str(self.data_root),
            "unit_dir": str(self.unit_dir),
            "forced_root": False,
        }

    def stop_disable_commands(self) -> dict[str, str]:
        return {
            "kill_switch": "nexo-node stop",
            "user_stop": "systemctl --user stop nexo-node.service",
            "user_disable": "systemctl --user disable --now nexo-node.service",
            "note": "User unit is optional and disabled by default in S14.",
        }
