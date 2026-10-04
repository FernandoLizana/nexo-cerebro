"""
Gobernador de descompresión — presupuesto por tick para materializar engramas y chunks.

Evita saturar RAM/latencia al multiplicar capacidad en disco.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DecompressionGovernor:
    max_bytes_per_tick: int = 262_144
    max_assemblies: int = 12
    max_chunks: int = 4
    prefetch_budget_bytes: int = 48_768
    bytes_used: int = 0
    assemblies_used: int = 0
    chunks_used: int = 0
    prefetch_bytes_used: int = 0
    blocked: int = 0
    prefetch_blocked: int = 0
    priority_boost: float = 0.0
    prefetch_warmed: int = 0
    lobe_budgets: dict[str, int] = field(default_factory=dict)
    lobe_bytes_used: dict[str, int] = field(default_factory=dict)
    lifetime_bytes: int = 0
    lifetime_prefetch_bytes: int = 0
    lifetime_blocked: int = 0
    lifetime_ticks: int = 0
    _log: list[str] = field(default_factory=list)

    def reset_tick(self) -> None:
        self.bytes_used = 0
        self.assemblies_used = 0
        self.chunks_used = 0
        self.prefetch_bytes_used = 0
        self.blocked = 0
        self.prefetch_blocked = 0
        self.priority_boost = 0.0
        self.prefetch_warmed = 0
        self.lobe_bytes_used = {}

    def configure_lobe_budgets(self, per_lobe: int) -> None:
        cap = max(8192, int(per_lobe))
        self.lobe_budgets = {
            "occipital": cap,
            "temporal": cap,
            "parietal": cap,
            "frontal": cap,
        }

    def can_spend_lobe(self, lobe: str, nbytes: int, *, kind: str = "generic") -> bool:
        cap = self.lobe_budgets.get(lobe, self.max_bytes_per_tick // 4)
        used = self.lobe_bytes_used.get(lobe, 0)
        if used + nbytes > cap:
            return False
        return self.can_spend(nbytes, kind=kind)

    def record_lobe(self, lobe: str, nbytes: int, *, kind: str = "generic", label: str = "") -> bool:
        if not self.can_spend_lobe(lobe, nbytes, kind=kind):
            self.blocked += 1
            return False
        if not self.record(nbytes, kind=kind, label=label):
            return False
        self.lobe_bytes_used[lobe] = self.lobe_bytes_used.get(lobe, 0) + max(0, nbytes)
        return True

    def finalize_tick(self) -> None:
        self.lifetime_bytes += self.bytes_used
        self.lifetime_prefetch_bytes += self.prefetch_bytes_used
        self.lifetime_blocked += self.blocked + self.prefetch_blocked
        self.lifetime_ticks += 1

    def set_priorities(
        self,
        *,
        conscious_salience: float = 0.0,
        surprise: float = 0.0,
        remembered: bool = False,
    ) -> None:
        boost = conscious_salience * 0.35 + surprise * 0.25
        if remembered:
            boost += 0.12
        self.priority_boost = float(min(1.0, boost))

    def effective_assembly_limit(self, base_k: int) -> int:
        extra = int(self.priority_boost * 4)
        cap = self.max_assemblies - self.assemblies_used
        return max(0, min(cap, base_k + extra))

    def can_spend(self, nbytes: int, *, kind: str = "generic") -> bool:
        if self.bytes_used + nbytes > self.max_bytes_per_tick:
            return False
        if kind == "assembly" and self.assemblies_used >= self.max_assemblies + int(
            self.priority_boost * 3
        ):
            return False
        if kind == "chunk" and self.chunks_used >= self.max_chunks + (
            1 if self.priority_boost > 0.4 else 0
        ):
            return False
        return True

    def can_prefetch(self, nbytes: int) -> bool:
        return self.prefetch_bytes_used + nbytes <= self.prefetch_budget_bytes

    def record(self, nbytes: int, *, kind: str = "generic", label: str = "") -> bool:
        if not self.can_spend(nbytes, kind=kind):
            self.blocked += 1
            if label:
                self._log.insert(0, f"bloqueado: {label[:40]}")
                self._log = self._log[:5]
            return False
        self.bytes_used += max(0, nbytes)
        if kind == "assembly":
            self.assemblies_used += 1
        elif kind == "chunk":
            self.chunks_used += 1
        return True

    def record_prefetch(self, nbytes: int, *, label: str = "") -> bool:
        if not self.can_prefetch(nbytes):
            self.prefetch_blocked += 1
            return False
        self.prefetch_bytes_used += max(0, nbytes)
        self.prefetch_warmed += 1
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_bytes_per_tick": self.max_bytes_per_tick,
            "bytes_used": self.bytes_used,
            "bytes_pct": round(100.0 * self.bytes_used / max(self.max_bytes_per_tick, 1), 1),
            "prefetch_budget_bytes": self.prefetch_budget_bytes,
            "prefetch_bytes_used": self.prefetch_bytes_used,
            "prefetch_pct": round(
                100.0 * self.prefetch_bytes_used / max(self.prefetch_budget_bytes, 1), 1
            ),
            "assemblies_used": self.assemblies_used,
            "max_assemblies": self.max_assemblies,
            "chunks_used": self.chunks_used,
            "max_chunks": self.max_chunks,
            "priority_boost": round(self.priority_boost, 3),
            "blocked": self.blocked,
            "prefetch_blocked": self.prefetch_blocked,
            "prefetch_warmed": self.prefetch_warmed,
            "lobe_budgets": dict(self.lobe_budgets),
            "lobe_bytes_used": dict(self.lobe_bytes_used),
            "log": self._log[:4],
            **self.cumulative_dict(),
        }

    def cumulative_dict(self) -> dict[str, Any]:
        return {
            "lifetime_bytes": self.lifetime_bytes,
            "lifetime_prefetch_bytes": self.lifetime_prefetch_bytes,
            "lifetime_blocked": self.lifetime_blocked,
            "lifetime_ticks": self.lifetime_ticks,
        }

    def load_cumulative(self, data: dict[str, Any] | None) -> None:
        if not data:
            return
        self.lifetime_bytes = int(data.get("lifetime_bytes", self.lifetime_bytes))
        self.lifetime_prefetch_bytes = int(
            data.get("lifetime_prefetch_bytes", self.lifetime_prefetch_bytes)
        )
        self.lifetime_blocked = int(data.get("lifetime_blocked", self.lifetime_blocked))
        self.lifetime_ticks = int(data.get("lifetime_ticks", self.lifetime_ticks))
