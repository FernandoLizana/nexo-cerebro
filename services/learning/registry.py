"""Artifact registry with active pointer and rollback history."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.learning.models import ArtifactStatus, LearningArtifact


class RegistryError(ValueError):
    pass


class ArtifactRegistry:
    """Disk registry under ``root/{artifacts,active.json,history.jsonl}``."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.artifacts_dir = self.root / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.active_path = self.root / "active.json"
        self.history_path = self.root / "history.jsonl"
        meta = self.root / "meta.json"
        if not meta.is_file():
            _write_json(
                meta,
                {
                    "format_version": "learning-registry-v1",
                    "auto_deploy": False,
                    "manual_promote_only": True,
                },
            )

    def save(self, artifact: LearningArtifact) -> Path:
        path = self.artifacts_dir / f"{artifact.artifact_id}.json"
        _write_json(path, artifact.to_dict())
        return path

    def load(self, artifact_id: str) -> LearningArtifact:
        path = self.artifacts_dir / f"{artifact_id}.json"
        if not path.is_file():
            raise RegistryError(f"artifact not found: {artifact_id}")
        return LearningArtifact.from_dict(_read_json(path))

    def set_active(self, artifact: LearningArtifact) -> None:
        if artifact.status is not ArtifactStatus.PROMOTED:
            raise RegistryError("only PROMOTED artifacts may become active")
        _write_json(
            self.active_path,
            {
                "artifact_id": artifact.artifact_id,
                "manual_promote_only": True,
                "auto_deploy": False,
            },
        )
        self._append_history({"action": "activate", "artifact_id": artifact.artifact_id})

    def get_active(self) -> LearningArtifact | None:
        if not self.active_path.is_file():
            return None
        data = _read_json(self.active_path)
        aid = data.get("artifact_id")
        if not aid:
            return None
        return self.load(str(aid))

    def clear_active(self) -> None:
        if self.active_path.is_file():
            self.active_path.unlink()
        self._append_history({"action": "clear_active"})

    def _append_history(self, event: dict[str, Any]) -> None:
        with self.history_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")

    def history(self) -> list[dict[str, Any]]:
        if not self.history_path.is_file():
            return []
        out: list[dict[str, Any]] = []
        for line in self.history_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
        return out


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
