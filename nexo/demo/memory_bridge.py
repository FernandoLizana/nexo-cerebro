"""Puente advisory memoria legacy SQLite ↔ HippocampalStore integrado (Fase 13)."""

from __future__ import annotations

from typing import Any


def _legacy_memory_count(brain: Any) -> int:
    store = getattr(brain, "memory_store", None)
    if store is None:
        return 0
    if hasattr(store, "total_count"):
        return int(store.total_count())
    hot = getattr(store, "hot_entries", None)
    if hot is not None:
        return len(hot)
    return 0


def _integrated_memory_count(runtime: Any) -> int:
    store = runtime.scheduler.config.get("hippocampal_store")
    if store is None:
        return 0
    return len(getattr(store, "episodes", []) or [])


def sync_memory_bridge_advisory(brain: Any, runtime: Any) -> dict[str, Any]:
    """Compara conteos legacy/integrado; no fusiona almacenes (advisory)."""
    legacy_n = _legacy_memory_count(brain)
    integrated_n = _integrated_memory_count(runtime)
    denom = max(legacy_n, integrated_n, 1)
    parity = min(legacy_n, integrated_n) / denom
    return {
        "synced": True,
        "legacy_count": legacy_n,
        "integrated_count": integrated_n,
        "parity_ratio": parity,
        "bridge_mode": "advisory",
    }
