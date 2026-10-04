"""
Formación hipocampal: DG (patrón sparse) → CA3 (atractor) → CA1 (salida).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .neuron import LIFPopulation
from .synapse import SparseSynapses


@dataclass
class HippocampalFormation:
    n_in: int
    n_dg: int
    n_ca3: int
    n_ca1: int
    dg_sparsity: float = 0.12

    dg: LIFPopulation = field(init=False)
    ca3: LIFPopulation = field(init=False)
    ca1: LIFPopulation = field(init=False)
    in_to_dg: SparseSynapses = field(init=False)
    dg_to_ca3: SparseSynapses = field(init=False)
    ca3_recur: SparseSynapses = field(init=False)
    ca3_to_ca1: SparseSynapses = field(init=False)

    def __post_init__(self) -> None:
        rng = np.random.default_rng(23)
        self.dg = LIFPopulation(self.n_dg, tau_ms=12.0, v_thresh=-54.0)
        self.ca3 = LIFPopulation(self.n_ca3, tau_ms=18.0, v_thresh=-53.0)
        self.ca1 = LIFPopulation(self.n_ca1, tau_ms=20.0, v_thresh=-53.0)
        d = 0.16
        self.in_to_dg = SparseSynapses(self.n_in, self.n_dg, density=d, rng=rng)
        self.dg_to_ca3 = SparseSynapses(self.n_dg, self.n_ca3, density=d * 0.95, rng=rng)
        self.ca3_recur = SparseSynapses(self.n_ca3, self.n_ca3, density=d * 0.45, rng=rng)
        self.ca3_to_ca1 = SparseSynapses(self.n_ca3, self.n_ca1, density=d, rng=rng)

    @property
    def n_neurons(self) -> int:
        return self.n_dg + self.n_ca3 + self.n_ca1

    def reset(self) -> None:
        self.dg.reset()
        self.ca3.reset()
        self.ca1.reset()

    def _enforce_dg_sparsity(self) -> None:
        k = max(1, int(self.n_dg * self.dg_sparsity))
        if float(self.dg.v.max()) <= self.dg.v_thresh:
            self.dg.spikes.fill(False)
            return
        idx = np.argpartition(self.dg.v, -k)[-k:]
        mask = np.zeros(self.n_dg, dtype=np.bool_)
        mask[idx] = True
        self.dg.spikes = mask & (self.dg.v >= self.dg.v_thresh)

    def step(
        self,
        sensory: np.ndarray,
        *,
        gain: float,
        theta_amp: float,
        mode: str,
        stress: float = 0.0,
    ) -> np.ndarray:
        ext = np.asarray(sensory, dtype=np.float32).ravel()
        if ext.size < self.n_in:
            ext = np.pad(ext, (0, self.n_in - ext.size))
        ext = ext[: self.n_in]
        stress_damp = float(np.clip(1.0 - 0.45 * max(0.0, stress - 0.25), 0.35, 1.0))
        drive = np.clip(ext * 24.0 * theta_amp * stress_damp, 0, 38)

        z_dg = np.zeros(self.n_dg, dtype=np.float32)
        z_ca3 = np.zeros(self.n_ca3, dtype=np.float32)
        z_ca1 = np.zeros(self.n_ca1, dtype=np.float32)
        pre = (drive > 1.0).astype(np.bool_)
        i_dg = self.in_to_dg.forward(pre) * gain + drive[: self.n_dg] * 0.15
        self.dg.integrate(z_dg, i_dg)
        self._enforce_dg_sparsity()

        i_ca3 = self.dg_to_ca3.forward(self.dg.spikes) * gain
        i_ca3 += self.ca3_recur.forward(self.ca3.spikes) * gain * 0.55
        self.ca3.integrate(i_ca3, z_ca3)

        i_ca1 = self.ca3_to_ca1.forward(self.ca3.spikes) * gain
        if mode == "retrieve":
            i_ca1 = i_ca1 * 1.12
        self.ca1.integrate(i_ca1, z_ca1)

        out = np.zeros(self.n_in, dtype=np.float32)
        n = min(self.n_ca1, self.n_in)
        norm = max(float(np.abs(self.ca1.v[:n]).max()), 1e-5)
        out[:n] = np.clip(self.ca1.v[:n] / norm, 0, 1)
        return out
