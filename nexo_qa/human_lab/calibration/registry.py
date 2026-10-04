"""Calibration registry."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from nexo_qa.human_lab.models import CalibrationRecord


@dataclass
class CalibrationRegistry:
    records: dict[str, CalibrationRecord] = field(default_factory=dict)

    def register(self, record: CalibrationRecord) -> CalibrationRecord:
        if not record.created_at:
            record.created_at = datetime.now(timezone.utc).isoformat()
        self.records[record.calibration_id] = record
        return record

    def get(self, calibration_id: str) -> CalibrationRecord | None:
        return self.records.get(calibration_id)

    def to_dict(self) -> dict:
        return {"records": {k: v.to_dict() for k, v in self.records.items()}}

    def write_json(self, path: Path | str) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load_json(cls, path: Path | str) -> CalibrationRegistry:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        reg = cls()
        for cid, raw in (data.get("records") or {}).items():
            reg.records[cid] = CalibrationRecord(
                calibration_id=cid,
                status=raw.get("status", "EXPERIMENTAL"),
                dataset_id=str(raw.get("dataset_id", "")),
                domain_id=str(raw.get("domain_id", "")),
                metrics_version=str(raw.get("metrics_version", "metrics-v1")),
                taxonomy_version=str(raw.get("taxonomy_version", "failures-v1")),
                persona_version=int(raw.get("persona_version", 1)),
                model_versions=dict(raw.get("model_versions") or {}),
                validation_results=dict(raw.get("validation_results") or {}),
                hfp_claim_allowed=bool(raw.get("hfp_claim_allowed", False)),
                created_at=str(raw.get("created_at", "")),
            )
        return reg
