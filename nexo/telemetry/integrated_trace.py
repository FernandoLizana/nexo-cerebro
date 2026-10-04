"""Trazabilidad integrada por tick — Sprint 15."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class IntegratedTraceCollector:
    """Registro compacto de señales observables por tick."""

    entries: list[dict[str, Any]] = field(default_factory=list)
    max_entries: int = 5000

    def record_tick(
        self,
        *,
        tick: int,
        action: str | None,
        energy: float,
        deliveries: int,
        config: dict[str, Any],
    ) -> None:
        entry = {
            "tick": tick,
            "action": action,
            "energy": round(float(energy), 5),
            "deliveries": int(deliveries),
            "wm_gain": round(float(config.get("connectome_wm_route_gain", 0.0) or 0.0), 5),
            "episodic_gain": round(float(config.get("connectome_episodic_route_gain", 0.0) or 0.0), 5),
            "workspace_gain": round(float(config.get("connectome_workspace_route_gain", 0.0) or 0.0), 5),
        }
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries :]

    def summary(self) -> dict[str, Any]:
        if not self.entries:
            return {"ticks": 0, "mean_energy": 0.0, "total_deliveries": 0}
        energies = [float(e["energy"]) for e in self.entries]
        return {
            "ticks": len(self.entries),
            "mean_energy": round(sum(energies) / len(energies), 5),
            "total_deliveries": sum(int(e["deliveries"]) for e in self.entries),
            "ticks_with_wm_gain": sum(1 for e in self.entries if float(e.get("wm_gain", 0)) > 0),
        }

    def to_dict(self) -> dict[str, Any]:
        return {"summary": self.summary(), "entries": self.entries}

    def export_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
