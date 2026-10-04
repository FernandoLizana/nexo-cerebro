"""Esquema estándar de resultados experimentales."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "1.0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def trajectory_hash(trajectory: list[dict[str, Any]]) -> str:
    raw = json.dumps(trajectory, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class ExperimentResult:
    schema_version: str = SCHEMA_VERSION
    experiment: str = ""
    condition: str = ""
    seed: int = 0
    commit: str = ""
    dirty_repository: bool = False
    started_at: str = ""
    finished_at: str = ""
    python_version: str = field(default_factory=lambda: sys.version.split()[0])
    platform: str = field(default_factory=platform.platform)
    config_hash: str = ""
    flags: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    trajectory_hash: str = ""
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def finish(self) -> None:
        self.finished_at = _utc_now()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def start(
        cls,
        *,
        experiment: str,
        condition: str,
        seed: int,
        config_hash: str,
        flags: dict[str, Any],
        parameters: dict[str, Any] | None = None,
        commit: str = "",
        dirty: bool = False,
    ) -> ExperimentResult:
        return cls(
            experiment=experiment,
            condition=condition,
            seed=seed,
            commit=commit,
            dirty_repository=dirty,
            started_at=_utc_now(),
            config_hash=config_hash,
            flags=flags,
            parameters=parameters or {},
        )

    def validate_required(self) -> list[str]:
        missing = []
        for key in ("experiment", "condition", "config_hash", "flags"):
            if not getattr(self, key):
                missing.append(key)
        return missing
