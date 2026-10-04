"""On-disk runtime records for background Swarm processes (not secrets)."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RuntimeRecord:
    service: str
    pid: int
    argv: list[str]
    started_at: float
    data_dir: str
    host: str | None = None
    port: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuntimeRecord:
        return cls(
            service=str(data["service"]),
            pid=int(data["pid"]),
            argv=[str(x) for x in data.get("argv") or []],
            started_at=float(data.get("started_at") or time.time()),
            data_dir=str(data.get("data_dir") or ""),
            host=data.get("host"),
            port=int(data["port"]) if data.get("port") is not None else None,
            extra=dict(data.get("extra") or {}),
        )


def default_record_path(data_dir: Path | str, service: str) -> Path:
    return Path(data_dir) / f"{service}.runtime.json"


def save_runtime_record(path: Path | str, record: RuntimeRecord) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(record.to_dict(), indent=2) + "\n", encoding="utf-8")
    return p


def load_runtime_record(path: Path | str) -> RuntimeRecord | None:
    p = Path(path)
    if not p.is_file():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return None
    return RuntimeRecord.from_dict(data)


def clear_runtime_record(path: Path | str) -> None:
    p = Path(path)
    if p.is_file():
        p.unlink()
