"""Install layout and clean uninstall plan (no leftover services)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# NEXO must not register Windows services in S13.
FORBIDDEN_SERVICE_NAMES: frozenset[str] = frozenset(
    {
        "NEXONode",
        "NEXO-Node",
        "nexo-node",
        "NexoLabService",
    }
)


@dataclass
class InstallLayout:
    """User-local install roots — no Program Files service registration."""

    install_root: Path
    data_root: Path
    exe_name: str = "NEXO-Node.exe"
    consent_name: str = "consent.json"
    create_startup_entry: bool = False  # always False in S13

    def __post_init__(self) -> None:
        self.install_root = Path(self.install_root)
        self.data_root = Path(self.data_root)
        if self.create_startup_entry:
            raise ValueError("S13 forbids automatic startup entries")

    @classmethod
    def default_user_layout(cls) -> InstallLayout:
        local = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
        root = local / "NEXO" / "Node"
        return cls(install_root=root, data_root=root / "data")

    @property
    def exe_path(self) -> Path:
        return self.install_root / self.exe_name

    @property
    def consent_path(self) -> Path:
        return self.install_root / self.consent_name

    def expected_paths(self) -> list[Path]:
        return [
            self.install_root,
            self.exe_path,
            self.consent_path,
            self.data_root,
            self.install_root / "uninstall.json",
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "install_root": str(self.install_root),
            "data_root": str(self.data_root),
            "exe_name": self.exe_name,
            "create_startup_entry": False,
            "windows_service": None,
            "forbidden_services": sorted(FORBIDDEN_SERVICE_NAMES),
            "kill_switch": "NEXO-Node.exe stop   OR   nexo-node stop",
            "update_channel": "manual",
        }


def uninstall_plan(layout: InstallLayout) -> dict[str, Any]:
    """Describe a clean uninstall: delete install tree; assert no services left."""
    return {
        "remove_paths": [str(p) for p in layout.expected_paths()],
        "remove_windows_services": [],  # none were installed
        "verify_no_services": sorted(FORBIDDEN_SERVICE_NAMES),
        "kill_switch_before_uninstall": True,
        "notes": [
            "Stop the node (kill switch) before deleting files.",
            "S13 does not register a Windows Service — nothing to sc delete.",
            "Identity keys under data_root are removed with the tree unless backed up.",
        ],
    }


def write_uninstall_manifest(layout: InstallLayout) -> Path:
    path = layout.install_root / "uninstall.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "layout": layout.to_dict(),
        "plan": uninstall_plan(layout),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def simulate_uninstall(layout: InstallLayout, *, dry_run: bool = True) -> dict[str, Any]:
    """Remove install_root contents when dry_run is False; always report leftover check."""
    removed: list[str] = []
    if not dry_run and layout.install_root.exists():
        # Only delete under install_root — never touch arbitrary paths.
        for path in sorted(layout.install_root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
                removed.append(str(path))
            elif path.is_dir():
                try:
                    path.rmdir()
                    removed.append(str(path))
                except OSError:
                    pass
        if layout.install_root.exists():
            try:
                layout.install_root.rmdir()
                removed.append(str(layout.install_root))
            except OSError:
                pass
    leftovers = [str(p) for p in layout.expected_paths() if p.exists()]
    return {
        "dry_run": dry_run,
        "removed": removed,
        "leftovers": leftovers if not dry_run else [],
        "services_registered": [],
        "clean": (not dry_run and not leftovers) or dry_run,
        "plan": uninstall_plan(layout),
    }
