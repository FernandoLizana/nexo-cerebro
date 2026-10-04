"""Allowlisted job types for NEXO Node (fail closed)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


ALLOWED_JOB_TYPES: frozenset[str] = frozenset(
    {
        "RUN_TEXTWORLD_EXPERIMENT",
        "RUN_BEING_INTERACTION",
        "RUN_BROWSERWORLD_EXPERIMENT",
        "RUN_NODE_SELF_CHECK",
        "CREATE_BEING",
        "LIST_BEINGS",
        "RUN_CREATURE_SIMULATION",
    }
)

FORBIDDEN_JOB_PREFIXES: tuple[str, ...] = (
    "EXECUTE_SHELL",
    "INSTALL_PACKAGE",
    "OPEN_URL",
    "READ_PATH",
    "SCAN_",
)


class JobRejected(ValueError):
    """Unknown or forbidden job type."""


@dataclass(frozen=True, slots=True)
class JobRequest:
    job_type: str
    job_id: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        name = str(self.job_type or "").strip()
        if not name:
            raise JobRejected("empty job_type")
        upper = name.upper()
        for prefix in FORBIDDEN_JOB_PREFIXES:
            if upper.startswith(prefix):
                raise JobRejected(f"forbidden job type: {name}")
        if name not in ALLOWED_JOB_TYPES:
            raise JobRejected(f"job type not allowlisted: {name}")
