"""Population state — checkpoint and resume."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from nexo_qa.population.models import RunExecutionRecord, RunStatus


@dataclass
class PopulationState:
    population_id: str
    spec_hash: str
    plan_hash: str
    records: dict[str, RunExecutionRecord] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "population_id": self.population_id,
            "spec_hash": self.spec_hash,
            "plan_hash": self.plan_hash,
            "records": {k: v.to_dict() for k, v in self.records.items()},
        }

    def write_json(self, path: Path | str) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def from_dict(cls, data: dict) -> PopulationState:
        records = {
            k: RunExecutionRecord.from_dict(v) for k, v in (data.get("records") or {}).items()
        }
        return cls(
            population_id=str(data["population_id"]),
            spec_hash=str(data.get("spec_hash", "")),
            plan_hash=str(data.get("plan_hash", "")),
            records=records,
        )

    @classmethod
    def load_json(cls, path: Path | str) -> PopulationState:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def pending_run_ids(self, all_run_ids: list[str]) -> list[str]:
        pending: list[str] = []
        for rid in all_run_ids:
            rec = self.records.get(rid)
            if rec is None:
                pending.append(rid)
            elif rec.status in (RunStatus.FAILED_INFRASTRUCTURE, RunStatus.PLANNED, RunStatus.QUEUED):
                pending.append(rid)
        return pending

    def completed_count(self) -> int:
        return sum(1 for r in self.records.values() if r.status == RunStatus.COMPLETED)
