"""Append-only filesystem layout for quarantine / rejected / promoted."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from services.experience.models import ExperienceCandidate, ExperienceStatus


class ExperienceStoreError(ValueError):
    pass


class AppendOnlyExperienceStore:
    """Disk layout under ``root/{quarantine,validated,rejected,promoted}/``.

    Append-only: status transitions write a new file in the target dir and
    leave an audit copy; never silently overwrite quarantine history.
    """

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        for name in ("quarantine", "validated", "rejected", "promoted", "audit"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        meta = self.root / "meta.json"
        if not meta.is_file():
            _write_json(
                meta,
                {
                    "format_version": "experience-store-v1",
                    "auto_promote": False,
                    "note": "Promotion requires explicit promote(); never automatic.",
                },
            )

    def _dir_for(self, status: ExperienceStatus) -> Path:
        mapping = {
            ExperienceStatus.QUARANTINED: "quarantine",
            ExperienceStatus.VALIDATED: "validated",
            ExperienceStatus.REJECTED: "rejected",
            ExperienceStatus.PROMOTED: "promoted",
        }
        return self.root / mapping[status]

    def write(self, candidate: ExperienceCandidate) -> Path:
        # Active pointer: only one status dir holds the live record; audit keeps history.
        for status in ExperienceStatus:
            stale = self._dir_for(status) / f"{candidate.candidate_id}.json"
            if stale.is_file() and status is not candidate.status:
                stale.unlink()
        path = self._dir_for(candidate.status) / f"{candidate.candidate_id}.json"
        _write_json(path, candidate.to_dict())
        # Audit trail (append-only copies keyed by status)
        audit = (
            self.root
            / "audit"
            / f"{candidate.candidate_id}.{candidate.status.value.lower()}.json"
        )
        _write_json(audit, candidate.to_dict())
        return path

    def load(self, candidate_id: str) -> ExperienceCandidate:
        # Prefer latest lifecycle: promoted > validated > quarantine > rejected
        for status in (
            ExperienceStatus.PROMOTED,
            ExperienceStatus.VALIDATED,
            ExperienceStatus.QUARANTINED,
            ExperienceStatus.REJECTED,
        ):
            path = self._dir_for(status) / f"{candidate_id}.json"
            if path.is_file():
                return ExperienceCandidate.from_dict(_read_json(path))
        raise ExperienceStoreError(f"candidate not found: {candidate_id}")

    def list_status(self, status: ExperienceStatus) -> list[ExperienceCandidate]:
        out: list[ExperienceCandidate] = []
        for path in sorted(self._dir_for(status).glob("*.json")):
            out.append(ExperienceCandidate.from_dict(_read_json(path)))
        return out

    def list_quarantine(self) -> list[ExperienceCandidate]:
        return self.list_status(ExperienceStatus.QUARANTINED)

    def list_promoted(self) -> list[ExperienceCandidate]:
        return self.list_status(ExperienceStatus.PROMOTED)

    def stats(self) -> dict:
        return {
            "quarantine": len(self.list_status(ExperienceStatus.QUARANTINED)),
            "validated": len(self.list_status(ExperienceStatus.VALIDATED)),
            "rejected": len(self.list_status(ExperienceStatus.REJECTED)),
            "promoted": len(self.list_status(ExperienceStatus.PROMOTED)),
            "auto_promote": False,
        }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
