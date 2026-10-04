"""
Memoria de trabajo prefrontal: capacidad limitada + interferencia por sobrecarga.

No elige acciones. Si está llena, los ítems nuevos desplazan los de menor
saliencia y sube ``load`` → el priming PFC se debilita (agency sigue en
deliberación, pero con WM más ruidosa).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkingMemory:
    capacity: int = 7
    slots: list[dict] = field(default_factory=list)
    # Métricas de carga (Sprint S3)
    load: float = 0.0
    interference: float = 0.0
    drops: int = 0
    last_evicted: str = ""
    limited: bool = True  # si False, capacidad efectiva muy alta (modo paper legacy)

    def effective_capacity(self) -> int:
        return self.capacity if self.limited else max(self.capacity, 64)

    def push(
        self,
        *,
        label: str,
        modality: str = "world",
        room: str = "",
        remembered: bool = False,
        valence: float = 0.0,
        goal: str | None = None,
        actor: str = "nexo",
        tags: list[str] | None = None,
        salience: float = 0.5,
    ) -> None:
        key = f"{label}|{room}|{modality}"
        self.slots = [s for s in self.slots if s.get("key") != key]
        entry = {
            "key": key,
            "label": label[:80],
            "modality": modality,
            "room": room,
            "remembered": remembered,
            "valence": round(valence, 3),
            "goal": goal,
            "actor": actor,
            "tags": list(tags or [])[:4],
            "salience": float(max(0.0, min(1.0, salience))),
            "ts": time.time(),
        }
        self.slots.insert(0, entry)
        cap = self.effective_capacity()
        while len(self.slots) > cap:
            # Expulsa menor saliencia (empate → más antiguo al final)
            victim_i = min(
                range(1, len(self.slots)),
                key=lambda i: (self.slots[i].get("salience", 0.0), -self.slots[i].get("ts", 0)),
                default=len(self.slots) - 1,
            )
            if victim_i <= 0:
                victim_i = len(self.slots) - 1
            victim = self.slots.pop(victim_i)
            self.drops += 1
            self.last_evicted = str(victim.get("label", ""))[:40]
            # Interferencia: ítems restantes pierden un poco de saliencia
            for s in self.slots:
                s["salience"] = float(max(0.05, s.get("salience", 0.5) * 0.92))
        self._recompute_load()

    def _recompute_load(self) -> None:
        cap = max(1, self.effective_capacity())
        n = len(self.slots)
        self.load = float(min(1.0, n / cap))
        # Interferencia crece con load y drops recientes (saturada)
        self.interference = float(
            min(1.0, 0.55 * self.load + 0.08 * min(self.drops, 8) / 8.0)
        )

    def set_goal(self, goal: str | None) -> None:
        if not self.slots:
            self.slots.append(
                {
                    "key": "_goal",
                    "label": goal or "",
                    "goal": goal,
                    "salience": 0.7,
                    "ts": time.time(),
                }
            )
        else:
            self.slots[0]["goal"] = goal
        self._recompute_load()

    def snapshot(self) -> list[dict]:
        return [
            {k: v for k, v in s.items() if k not in ("key", "ts")}
            for s in self.slots
        ]

    def format_for_prompt(self) -> str:
        if not self.slots:
            return "—"
        lines: list[str] = []
        for s in self.slots[: self.effective_capacity()]:
            parts = [s.get("label", "?")]
            if s.get("room"):
                parts.append(f"@{s['room']}")
            if s.get("goal"):
                parts.append(f"meta:{s['goal']}")
            if s.get("remembered"):
                parts.append("(recuerdo)")
            lines.append(" · ".join(parts))
        return "\n".join(f"- {ln}" for ln in lines)

    def dominant_goal(self) -> str | None:
        for s in self.slots:
            g = s.get("goal")
            if g:
                return str(g)
        return None

    def pfc_gain_scale(self) -> float:
        """Escala [0.55, 1.0]: sobrecarga debilita priming PFC, no elige acción."""
        if not self.limited:
            return 1.0
        return float(max(0.55, 1.0 - 0.45 * self.interference))

    def clear(self) -> None:
        self.slots.clear()
        self.load = 0.0
        self.interference = 0.0
        self.drops = 0
        self.last_evicted = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "capacity": self.effective_capacity(),
            "n_slots": len(self.slots),
            "load": round(self.load, 3),
            "interference": round(self.interference, 3),
            "drops": self.drops,
            "last_evicted": self.last_evicted,
            "limited": self.limited,
            "pfc_gain_scale": round(self.pfc_gain_scale(), 3),
            "slots": self.snapshot()[:7],
        }
