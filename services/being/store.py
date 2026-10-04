"""Split Being persistence — IDENTITY / MEMORY / STATE / COGNITIVE CONFIG."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from services.being.models import (
    Being,
    BeingIdentity,
    CognitiveConfiguration,
    MemoryBundle,
    TemporaryState,
)
from services.being.validation import BeingValidationError, validate_being_parts

_SAFE_BEING_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _safe_being_id(being_id: str) -> str:
    raw = str(being_id or "").strip()
    if not _SAFE_BEING_ID.fullmatch(raw):
        raise BeingValidationError("invalid being_id")
    if ".." in raw or "/" in raw or "\\" in raw:
        raise BeingValidationError("invalid being_id")
    return raw


@dataclass(frozen=True, slots=True)
class BeingPaths:
    root: Path

    @property
    def identity(self) -> Path:
        return self.root / "identity.json"

    @property
    def memory_dir(self) -> Path:
        return self.root / "memory"

    @property
    def memory_index(self) -> Path:
        return self.memory_dir / "index.json"

    @property
    def state(self) -> Path:
        return self.root / "state.json"

    @property
    def cognitive(self) -> Path:
        return self.root / "cognitive.json"


class BeingStore:
    """Filesystem store under ``<beings_root>/<being_id>/``."""

    def __init__(self, beings_root: Path | str) -> None:
        self.beings_root = Path(beings_root).resolve()
        self.beings_root.mkdir(parents=True, exist_ok=True)

    def paths_for(self, being_id: str) -> BeingPaths:
        safe = _safe_being_id(being_id)
        root = (self.beings_root / safe).resolve()
        if root != self.beings_root and self.beings_root not in root.parents:
            raise BeingValidationError("being path escapes store root")
        return BeingPaths(root)

    def save(self, being: Being) -> BeingPaths:
        validate_being_parts(being.identity, being.memory, being.state, being.cognitive)
        paths = self.paths_for(being.identity.being_id)
        paths.root.mkdir(parents=True, exist_ok=True)
        paths.memory_dir.mkdir(parents=True, exist_ok=True)
        (paths.memory_dir / "episodic").mkdir(exist_ok=True)
        (paths.memory_dir / "semantic").mkdir(exist_ok=True)
        (paths.memory_dir / "relationships").mkdir(exist_ok=True)
        (paths.memory_dir / "summaries").mkdir(exist_ok=True)

        _write_json(paths.identity, being.identity.to_dict())
        _write_json(paths.memory_index, being.memory.to_dict())
        _write_json(paths.state, being.state.to_dict())
        _write_json(paths.cognitive, being.cognitive.to_dict())
        return paths

    def load(self, being_id: str) -> Being:
        paths = self.paths_for(being_id)
        if not paths.identity.is_file():
            raise BeingValidationError(f"being not found: {being_id}")
        identity = BeingIdentity.from_dict(_read_json(paths.identity))
        memory = MemoryBundle.from_dict(_read_json(paths.memory_index) if paths.memory_index.is_file() else {})
        state = TemporaryState.from_dict(_read_json(paths.state) if paths.state.is_file() else {})
        cognitive = CognitiveConfiguration.from_dict(
            _read_json(paths.cognitive) if paths.cognitive.is_file() else {}
        )
        validate_being_parts(identity, memory, state, cognitive)
        return Being(identity=identity, memory=memory, state=state, cognitive=cognitive)

    def list_ids(self) -> list[str]:
        if not self.beings_root.exists():
            return []
        ids = [
            p.name
            for p in sorted(self.beings_root.iterdir())
            if p.is_dir() and (p / "identity.json").is_file()
        ]
        return ids

    def exists(self, being_id: str) -> bool:
        return self.paths_for(being_id).identity.is_file()


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_no_monolith(paths: BeingPaths) -> None:
    """Guard: refuse a single giant being.json as the sole store."""
    monolith = paths.root / "being.json"
    if monolith.is_file() and not paths.identity.is_file():
        raise BeingValidationError(
            "legacy monolith being.json detected without split identity.json; migrate to split format"
        )
