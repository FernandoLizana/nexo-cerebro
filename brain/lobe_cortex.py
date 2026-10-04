"""
Columnas corticales por lóbulo — poblaciones LIF dedicadas que proyectan a la corteza.

Occipital → sensorial; temporal → límbico; parietal → asociativa; frontal → prefrontal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

from .neuron import LIFPopulation
from .synapse import SparseSynapses

if TYPE_CHECKING:
    from .cortex import CorticalNetwork


@dataclass
class LobeCorticalColumns:
    """Cuatro mini-columnas corticales acopladas a la red principal."""

    n_per_lobe: int = 24
    density: float = 0.14
    occipital: LIFPopulation = field(init=False)
    temporal: LIFPopulation = field(init=False)
    parietal: LIFPopulation = field(init=False)
    frontal: LIFPopulation = field(init=False)
    occ_to_s: SparseSynapses | None = field(default=None, init=False)
    temp_to_l: SparseSynapses | None = field(default=None, init=False)
    par_to_a: SparseSynapses | None = field(default=None, init=False)
    front_to_p: SparseSynapses | None = field(default=None, init=False)
    _buf_s: np.ndarray = field(init=False)
    _buf_l: np.ndarray = field(init=False)
    _buf_a: np.ndarray = field(init=False)
    _buf_p: np.ndarray = field(init=False)
    last: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ref = 2
        n = self.n_per_lobe
        self.occipital = LIFPopulation(n, tau_ms=12.0, refrac_ms=ref)
        self.temporal = LIFPopulation(n, tau_ms=16.0, v_thresh=-53.5, refrac_ms=ref)
        self.parietal = LIFPopulation(n, tau_ms=18.0, refrac_ms=ref)
        self.frontal = LIFPopulation(n, tau_ms=24.0, v_thresh=-51.0, refrac_ms=ref)

    @property
    def n_neurons(self) -> int:
        return 4 * self.n_per_lobe

    def bind_cortex(self, cortex: CorticalNetwork) -> None:
        n = self.n_per_lobe
        rng = np.random.default_rng(31)
        eta = 0.0028
        d = self.density
        self.occ_to_s = SparseSynapses(n, max(8, cortex.n_sensory // 4), density=d, rng=rng, eta=eta)
        self.temp_to_l = SparseSynapses(n, max(8, cortex.n_limbic // 4), density=d, rng=rng, eta=eta)
        self.par_to_a = SparseSynapses(n, max(8, cortex.n_associative // 4), density=d, rng=rng, eta=eta)
        self.front_to_p = SparseSynapses(n, max(8, cortex.n_prefrontal // 2), density=d, rng=rng, eta=eta)
        self._buf_s = np.zeros(self.occ_to_s.n_post, dtype=np.float32)
        self._buf_l = np.zeros(self.temp_to_l.n_post, dtype=np.float32)
        self._buf_a = np.zeros(self.par_to_a.n_post, dtype=np.float32)
        self._buf_p = np.zeros(self.front_to_p.n_post, dtype=np.float32)

    def _drive_pop(
        self,
        pop: LIFPopulation,
        vec: np.ndarray,
        syn: SparseSynapses,
        buf: np.ndarray,
    ) -> float:
        v = np.asarray(vec, dtype=np.float32).ravel()
        if v.size < pop.n:
            v = np.pad(v, (0, pop.n - v.size))
        ext = np.clip(v[: pop.n] * 26.0, 0, 36)
        z = np.zeros(pop.n, dtype=np.float32)
        pop.integrate(z, ext)
        pop.integrate(z, ext * 0.35)
        impulse = syn.forward(pop.spikes).astype(np.float32)
        if impulse.size != buf.size:
            impulse = impulse[: buf.size] if impulse.size > buf.size else np.pad(impulse, (0, buf.size - impulse.size))
        if not pop.spikes.any():
            impulse += float(np.clip((pop.v - pop.v_rest).mean(), 0, 4)) * 0.85
        buf[:] = buf * 0.82 + impulse * 0.9
        denom = max(pop.v_thresh - pop.v_rest, 1.0)
        act = float(np.clip((pop.v - pop.v_rest).mean() / denom, 0, 1.25))
        if pop.spikes.any():
            act = max(act, 0.65)
        return act

    def step(
        self,
        cortex: CorticalNetwork,
        *,
        vectors: dict[str, np.ndarray],
        gain: float = 1.0,
    ) -> dict[str, float]:
        if self.occ_to_s is None:
            self.bind_cortex(cortex)

        g = float(gain)
        activity = {
            "occipital": self._drive_pop(
                self.occipital, vectors.get("occipital", np.zeros(self.n_per_lobe)), self.occ_to_s, self._buf_s
            ),
            "temporal": self._drive_pop(
                self.temporal, vectors.get("temporal", np.zeros(self.n_per_lobe)), self.temp_to_l, self._buf_l
            ),
            "parietal": self._drive_pop(
                self.parietal, vectors.get("parietal", np.zeros(self.n_per_lobe)), self.par_to_a, self._buf_a
            ),
            "frontal": self._drive_pop(
                self.frontal, vectors.get("frontal", np.zeros(self.n_per_lobe)), self.front_to_p, self._buf_p
            ),
        }

        ns, nl, na, npf = cortex.n_sensory, cortex.n_limbic, cortex.n_associative, cortex.n_prefrontal
        boost_s = np.zeros(ns, dtype=np.float32)
        boost_l = np.zeros(nl, dtype=np.float32)
        boost_a = np.zeros(na, dtype=np.float32)
        boost_p = np.zeros(npf, dtype=np.float32)
        qs, ql, qa, qp = max(1, ns // 4), max(1, nl // 4), max(1, na // 4), max(1, npf // 2)
        boost_s[:qs] = self._buf_s[:qs] * 14.0 * g
        boost_l[:ql] = self._buf_l[:ql] * 12.0 * g
        boost_a[:qa] = self._buf_a[:qa] * 11.0 * g
        boost_p[:qp] = self._buf_p[:qp] * 10.0 * g

        cortex._lobe_boost_sensory = np.clip(
            getattr(cortex, "_lobe_boost_sensory", np.zeros(ns)) * 0.88 + boost_s, 0, 22
        )
        cortex._lobe_boost_limbic = np.clip(
            getattr(cortex, "_lobe_boost_limbic", np.zeros(nl)) * 0.88 + boost_l, 0, 20
        )
        cortex._lobe_boost_assoc = np.clip(
            getattr(cortex, "_lobe_boost_assoc", np.zeros(na)) * 0.88 + boost_a, 0, 18
        )
        cortex._lobe_boost_pfc = np.clip(
            getattr(cortex, "_lobe_boost_pfc", np.zeros(npf)) * 0.88 + boost_p, 0, 16
        )

        self.last = {"activity": {k: round(v, 3) for k, v in activity.items()}}
        return activity

    def activity_rows(self, width: int = 48) -> list[dict]:
        def row(pop: LIFPopulation, label: str, lid: str) -> dict:
            denom = max(pop.v_thresh - pop.v_rest, 1.0)
            act = np.clip((pop.v - pop.v_rest) / denom, 0, 1.25).astype(np.float32)
            act[pop.spikes] = 1.0
            x_old = np.linspace(0, 1, max(act.size, 1))
            x_new = np.linspace(0, 1, width)
            vals = np.interp(x_new, x_old, act).round(3).tolist() if act.size else [0.0] * width
            return {"id": lid, "label": label, "values": vals}

        return [
            row(self.occipital, "Col. occipital", "col_occ"),
            row(self.temporal, "Col. temporal", "col_temp"),
            row(self.parietal, "Col. parietal", "col_par"),
            row(self.frontal, "Col. frontal", "col_front"),
        ]

    def to_dict(self) -> dict:
        out = dict(self.last) if self.last else {}
        if self.last.get("activity"):
            out["columns"] = self.last["activity"]
        return out
