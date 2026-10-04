"""Grafo de conectoma con validación."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from nexo.connectome.connection import Connection


@dataclass
class ConnectomeGraph:
    version: str = "1"
    modules: set[str] = field(default_factory=set)
    connections: list[Connection] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> ConnectomeGraph:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        modules = set(data.get("modules", []))
        conns: list[Connection] = []
        for raw in data.get("connections", []):
            gating = raw.get("gating") or {}
            conns.append(
                Connection(
                    source=str(raw["source"]),
                    target=str(raw["target"]),
                    signal_type=str(raw.get("signal_type", "generic")),
                    weight=float(raw.get("weight", 1.0)),
                    latency_ticks=int(raw.get("latency_ticks", 1)),
                    excitatory=bool(raw.get("excitatory", True)),
                    plastic=bool(raw.get("plastic", False)),
                    bandwidth=float(raw.get("bandwidth", 1.0)),
                    noise=float(raw.get("noise", 0.0)),
                    reliability=float(raw.get("reliability", 1.0)),
                    minimum_gate=float(gating.get("minimum_gate", 0.0)),
                    gating_modulator=gating.get("modulator"),
                )
            )
        graph = cls(version=str(data.get("version", "1")), modules=modules, connections=conns)
        return graph

    def validate(self) -> list[str]:
        errors: list[str] = []
        known = set(self.modules)
        for c in self.connections:
            errors.extend(c.validate())
            if c.source not in known:
                errors.append(f"unknown_source:{c.source}")
            if c.target not in known:
                errors.append(f"unknown_target:{c.target}")
        orphans = known - {c.source for c in self.connections} - {c.target for c in self.connections}
        if len(known) > 1 and orphans:
            errors.append(f"orphan_modules:{sorted(orphans)}")
        return errors

    def outgoing(self, source: str) -> list[Connection]:
        return [c for c in self.connections if c.source == source]

    def to_graphml(self) -> str:
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
            '<graph id="nexo_connectome" edgedefault="directed">',
        ]
        for m in sorted(self.modules):
            lines.append(f'<node id="{m}"/>')
        for i, c in enumerate(self.connections):
            lines.append(
                f'<edge id="e{i}" source="{c.source}" target="{c.target}">'
                f'<data key="weight">{c.weight}</data></edge>'
            )
        lines.extend(["</graph>", "</graphml>"])
        return "\n".join(lines)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "modules": sorted(self.modules),
            "connections": [
                {
                    "source": c.source,
                    "target": c.target,
                    "signal_type": c.signal_type,
                    "weight": c.weight,
                    "latency_ticks": c.latency_ticks,
                }
                for c in self.connections
            ],
        }

    def export_reports(self, reports_dir: Path) -> None:
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / "CONNECTOME_GRAPH.graphml").write_text(self.to_graphml(), encoding="utf-8")
        (reports_dir / "CONNECTOME_GRAPH.json").write_text(
            json.dumps(self.to_json_dict(), indent=2), encoding="utf-8"
        )
