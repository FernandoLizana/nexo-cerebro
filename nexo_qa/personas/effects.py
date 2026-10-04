"""Persona effect audit — before/after mechanistic values."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from nexo_qa.personas.mapping import MECHANISTIC_MAP
from nexo_qa.personas.models import PersonaApplicationReport


@dataclass
class PersonaEffectAudit:
    persona_id: str
    entries: list[dict[str, Any]] = field(default_factory=list)

    def from_report(self, report: PersonaApplicationReport) -> PersonaEffectAudit:
        self.persona_id = report.persona_id
        for m in report.mappings:
            self.entries.append(
                {
                    "trait": m["trait"],
                    "module": m["module"],
                    "parameter": m["parameter"],
                    "requested": m["requested"],
                    "effective": m["effective"],
                    "effect": m["effect"],
                }
            )
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "entries": list(self.entries),
            "mechanistic_map_size": len(MECHANISTIC_MAP),
        }

    def write_json(self, path: Path | str) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
