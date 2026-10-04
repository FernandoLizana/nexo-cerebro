"""
Métricas por tick para experimentos E1–E3 (JSONL + agregados CSV).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from brain.deliberation import ACTION_SCHEMAS

_SCHEMA_DRIVE = {s["key"]: s["drive"] for s in ACTION_SCHEMAS}


@dataclass
class TickMetrics:
    tick: int = 0
    seed: int = 0
    condition: str = "full"
    choice_key: str = ""
    choice: str = ""
    agency: float = 0.0
    inhibited: bool = False
    spike_aligned: float = 0.0
    pfc_veto: bool = False
    remembered: bool = False
    surprise: float = 0.0
    drive_coherent: float = 0.0
    top_drive: str = ""
    agent_x: float = 0.0
    agent_y: float = 0.0
    room: str = ""
    motor: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def top_drive_name(drives: dict[str, float]) -> str:
    if not drives:
        return ""
    return max(drives.items(), key=lambda x: x[1])[0]


def drive_coherence(choice_key: str, drives: dict[str, float]) -> float:
    """1 si la acción elegida coincide con el drive dominante; 0 si no."""
    top = top_drive_name(drives)
    if not top or top == "seek_curiosity":
        return 0.5
    action_drive = _SCHEMA_DRIVE.get(choice_key, "")
    return 1.0 if action_drive == top else 0.0


def extract_tick_metrics(
    tick_out: dict[str, Any],
    *,
    tick: int,
    seed: int,
    condition: str,
) -> TickMetrics:
    delib = tick_out.get("deliberation") or {}
    ic = tick_out.get("intention_circuit") or {}
    drives = tick_out.get("drives") or {}
    world = tick_out.get("world") or {}
    agent = world.get("agent") or {}
    cog = tick_out.get("cognition") or {}
    pred = cog.get("prediction") or cog.get("last_summary", {}).get("prediction", {})
    surprise = float(pred.get("surprise", cog.get("prediction", {}).get("surprise", 0)))

    return TickMetrics(
        tick=tick,
        seed=seed,
        condition=condition,
        choice_key=str(delib.get("choice_key", "")),
        choice=str(delib.get("choice", "")),
        agency=float(delib.get("agency", 0)),
        inhibited=bool(delib.get("inhibited", False)),
        spike_aligned=float(ic.get("spike_aligned", 0)),
        pfc_veto=bool(ic.get("pfc_veto", False)),
        remembered=bool(tick_out.get("remembered", False)),
        surprise=surprise,
        drive_coherent=drive_coherence(str(delib.get("choice_key", "")), drives),
        top_drive=top_drive_name(drives),
        agent_x=float(agent.get("x", world.get("agent_x", 0))),
        agent_y=float(agent.get("y", world.get("agent_y", 0))),
        room=str(world.get("room", world.get("current_room", ""))),
        motor=list(tick_out.get("motor") or []),
    )


class MetricsLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._rows: list[TickMetrics] = []

    def log(self, row: TickMetrics) -> None:
        self._rows.append(row)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")

    @property
    def rows(self) -> list[TickMetrics]:
        return list(self._rows)

    def summary(self) -> dict[str, float]:
        if not self._rows:
            return {}
        n = len(self._rows)
        return {
            "n_ticks": n,
            "mean_agency": sum(r.agency for r in self._rows) / n,
            "mean_spike_aligned": sum(r.spike_aligned for r in self._rows) / n,
            "pfc_veto_rate": sum(1 for r in self._rows if r.pfc_veto) / n,
            "inhibited_rate": sum(1 for r in self._rows if r.inhibited) / n,
            "remembered_rate": sum(1 for r in self._rows if r.remembered) / n,
            "mean_surprise": sum(r.surprise for r in self._rows) / n,
            "mean_drive_coherent": sum(r.drive_coherent for r in self._rows) / n,
        }


def write_summary_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    import csv

    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
