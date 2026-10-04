"""
Connectome Scaffold — espacio lógico ~86B neuronas con seed fija (estilo mapa procedural).

No materializa 86B LIF: define direcciones, ratios humanos y densidades sinápticas
region×region para chunks lazy y métricas de escala.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "data" / "connectome" / "default_manifest.json"


@dataclass(frozen=True)
class RegionSpec:
    id: str
    volume_fraction: float
    module: str
    addr_start: int
    addr_end: int

    @property
    def neuron_count(self) -> int:
        return max(0, self.addr_end - self.addr_start)


@dataclass
class ConnectomeBlueprint:
    seed: int = 42
    logical_neurons: int = 86_000_000_000
    manifest_path: Path = field(default_factory=lambda: MANIFEST_PATH)
    regions: tuple[RegionSpec, ...] = field(default_factory=tuple)
    choice_key_region: dict[str, str] = field(default_factory=dict)
    synapse_density_global: float = 1.4e-4
    _local_density: dict[tuple[str, str], float] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if not self.regions:
            object.__setattr__(self, "regions", tuple(self._load_regions()))
        if not self.choice_key_region:
            object.__setattr__(self, "choice_key_region", self._load_choice_map())
        self._build_density_cache()

    def _load_manifest(self) -> dict:
        path = Path(self.manifest_path)
        if not path.is_file():
            return {
                "logical_neurons": self.logical_neurons,
                "synapse_density_global": self.synapse_density_global,
                "regions": [],
                "choice_key_region": {},
            }
        return json.loads(path.read_text(encoding="utf-8"))

    def _load_regions(self) -> list[RegionSpec]:
        data = self._load_manifest()
        logical = int(data.get("logical_neurons", self.logical_neurons))
        object.__setattr__(self, "logical_neurons", logical)
        object.__setattr__(
            self,
            "synapse_density_global",
            float(data.get("synapse_density_global", self.synapse_density_global)),
        )
        raw = data.get("regions") or []
        total_frac = sum(float(r.get("volume_fraction", 0)) for r in raw) or 1.0
        specs: list[RegionSpec] = []
        cursor = 0
        for r in raw:
            frac = float(r.get("volume_fraction", 0)) / total_frac
            count = max(1, int(logical * frac))
            specs.append(
                RegionSpec(
                    id=str(r["id"]),
                    volume_fraction=frac,
                    module=str(r.get("module", "")),
                    addr_start=cursor,
                    addr_end=cursor + count,
                )
            )
            cursor += count
        if cursor < logical and specs:
            last = specs[-1]
            specs[-1] = RegionSpec(
                id=last.id,
                volume_fraction=last.volume_fraction,
                module=last.module,
                addr_start=last.addr_start,
                addr_end=logical,
            )
        return specs

    def _load_choice_map(self) -> dict[str, str]:
        return dict(self._load_manifest().get("choice_key_region") or {})

    def _build_density_cache(self) -> None:
        ids = [r.id for r in self.regions]
        rng = np.random.default_rng(self.seed)
        for a in ids:
            for b in ids:
                base = self.synapse_density_global
                if a == b:
                    mult = 8.0
                elif a.split("_")[0] == b.split("_")[0]:
                    mult = 2.5
                else:
                    mult = float(rng.uniform(0.05, 0.35))
                self._local_density[(a, b)] = base * mult

    def region_for_choice(self, choice_key: str) -> str:
        return self.choice_key_region.get(choice_key, "lobe_frontal")

    def region_spec(self, region_id: str) -> RegionSpec | None:
        for r in self.regions:
            if r.id == region_id:
                return r
        return None

    def map_active_index(self, active_i: int, region_id: str) -> int:
        spec = self.region_spec(region_id)
        if spec is None or spec.neuron_count <= 0:
            return int(active_i)
        span = spec.neuron_count
        h = hash((self.seed, region_id, active_i)) & 0x7FFFFFFF
        return spec.addr_start + (h % span)

    def estimate_logical_synapses(self) -> int:
        total = 0
        for ra in self.regions:
            for rb in self.regions:
                d = self._local_density.get((ra.id, rb.id), self.synapse_density_global)
                total += int(ra.neuron_count * rb.neuron_count * d)
        return max(total, self.logical_neurons)

    def sample_synapses(
        self,
        region_a: str,
        region_b: str,
        k: int,
        *,
        tick: int = 0,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Muestra k pesos sparse procedurales (sin almacenar matriz completa)."""
        seed = hash((self.seed, region_a, region_b, tick)) & 0x7FFFFFFF
        rng = np.random.default_rng(seed)
        weights = rng.uniform(0.02, 0.35, size=max(1, k)).astype(np.float32)
        indices = rng.integers(0, max(64, k * 4), size=max(1, k), dtype=np.int32)
        return indices, weights

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "logical_neurons": self.logical_neurons,
            "logical_synapses_est": self.estimate_logical_synapses(),
            "regions": len(self.regions),
            "human_volume_fidelity": round(
                sum(r.volume_fraction for r in self.regions[:4]), 3
            ),
        }
