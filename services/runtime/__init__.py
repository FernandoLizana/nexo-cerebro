"""Shared Swarm interaction / process-runtime helpers (opt-in, localhost-safe)."""

from __future__ import annotations

from services.runtime.config import load_params_file, merge_params
from services.runtime.loopback import assert_loopback_host, is_loopback_host
from services.runtime.state import RuntimeRecord, load_runtime_record, save_runtime_record

__all__ = [
    "RuntimeRecord",
    "assert_loopback_host",
    "is_loopback_host",
    "load_params_file",
    "load_runtime_record",
    "merge_params",
    "save_runtime_record",
]
