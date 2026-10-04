"""Owner kill-switch verification for lab devices."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.node.runtime import NodeRuntime, NodeState


def verify_kill_switch(data_dir: Path | str, *, node_name: str = "lab-node") -> dict[str, Any]:
    """Start a local node, invoke kill switch, assert STOPPED and private key cleared."""
    runtime = NodeRuntime(data_dir=data_dir, node_name=node_name)
    runtime.start()
    assert runtime.state is NodeState.RUNNING
    assert runtime._private_key is not None  # noqa: SLF001 — lab verification surface
    snapshot = runtime.kill_switch(reason="S15 lab kill-switch verification")
    assert runtime.state is NodeState.STOPPED
    assert runtime._private_key is None  # noqa: SLF001
    return {
        "ok": True,
        "state": snapshot.get("state"),
        "reason": snapshot.get("reason"),
        "networking_enabled": snapshot.get("networking_enabled", False),
        "private_key_in_memory": False,
    }
