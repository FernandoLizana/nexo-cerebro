"""Microcircuitos inhibitorios (interneuronas, ratio E/I ≈ 4:1)."""

from __future__ import annotations

import numpy as np

from .neuron import LIFPopulation
from .synapse import SparseSynapses


class InhibitoryMicrocircuit:
    __slots__ = ("n_inh", "inh", "e_to_i", "i_to_e")

    def __init__(self, n_exc: int, *, density: float, rng: np.random.Generator, refrac_ms: int = 2) -> None:
        self.n_inh = max(4, n_exc // 5)
        self.inh = LIFPopulation(self.n_inh, tau_ms=7.5, v_thresh=-54.0, refrac_ms=refrac_ms)
        self.e_to_i = SparseSynapses(n_exc, self.n_inh, density=density * 1.15, rng=rng, w_init=0.7)
        self.i_to_e = SparseSynapses(
            self.n_inh, n_exc, density=density * 0.95, rng=rng, w_init=-0.9
        )

    def shunt(self, exc_spikes: np.ndarray, exc_current: np.ndarray) -> np.ndarray:
        z = np.zeros(self.n_inh, dtype=np.float32)
        self.inh.integrate(self.e_to_i.forward(exc_spikes), z)
        inh_i = self.i_to_e.forward(self.inh.spikes)
        return np.maximum(exc_current + inh_i, 0.0)

    def reset(self) -> None:
        self.inh.reset()


class SubtypeInhibitoryCircuit:
    """
    Interneuronas por subtipo — PV (rápida perisomática), SST (dendrítica), VIP (desinhibición).

    Aproximación funcional del microcircuito cortical humano.
    """

    __slots__ = ("n_pv", "n_sst", "n_vip", "pv", "sst", "vip", "e_to_pv", "pv_to_e", "e_to_sst", "sst_to_e", "vip_to_pv")

    def __init__(self, n_exc: int, *, density: float, rng: np.random.Generator, refrac_ms: int = 2) -> None:
        base = max(4, n_exc // 5)
        self.n_pv = max(2, base // 2)
        self.n_sst = max(2, base // 3)
        self.n_vip = max(2, base // 4)
        self.pv = LIFPopulation(self.n_pv, tau_ms=6.5, v_thresh=-54.0, refrac_ms=refrac_ms)
        self.sst = LIFPopulation(self.n_sst, tau_ms=12.0, v_thresh=-53.5, refrac_ms=refrac_ms)
        self.vip = LIFPopulation(self.n_vip, tau_ms=9.0, v_thresh=-54.0, refrac_ms=refrac_ms)
        self.e_to_pv = SparseSynapses(n_exc, self.n_pv, density=density * 1.2, rng=rng, w_init=0.75)
        self.pv_to_e = SparseSynapses(self.n_pv, n_exc, density=density, rng=rng, w_init=-1.0)
        self.e_to_sst = SparseSynapses(n_exc, self.n_sst, density=density * 0.85, rng=rng, w_init=0.55)
        self.sst_to_e = SparseSynapses(self.n_sst, n_exc, density=density * 0.7, rng=rng, w_init=-0.55)
        self.vip_to_pv = SparseSynapses(self.n_vip, self.n_pv, density=density * 0.6, rng=rng, w_init=-0.45)

    @property
    def n_inh(self) -> int:
        return self.n_pv + self.n_sst + self.n_vip

    def shunt(self, exc_spikes: np.ndarray, exc_current: np.ndarray) -> np.ndarray:
        z = np.zeros(max(self.n_pv, self.n_sst, self.n_vip), dtype=np.float32)
        cur = np.asarray(exc_current, dtype=np.float32)

        self.sst.integrate(self.e_to_sst.forward(exc_spikes), z[: self.n_sst])
        dend_inh = self.sst_to_e.forward(self.sst.spikes)
        cur = np.maximum(cur * 0.94 + dend_inh * 0.65, 0.0)

        self.pv.integrate(self.e_to_pv.forward(exc_spikes), z[: self.n_pv])
        pv_inh = self.pv_to_e.forward(self.pv.spikes)

        vip_drive = self.pv.spikes.astype(np.float32) * 3.0
        if vip_drive.size < self.n_vip:
            vip_drive = np.pad(vip_drive, (0, self.n_vip - vip_drive.size))
        self.vip.integrate(vip_drive[: self.n_vip], z[: self.n_vip])
        pv_disinh = self.vip_to_pv.forward(self.vip.spikes)
        if pv_disinh.size == pv_inh.size:
            pv_inh = pv_inh * (1.0 + float(np.clip(pv_disinh.mean(), -0.35, 0.15)))

        return np.maximum(cur + pv_inh, 0.0)

    def reset(self) -> None:
        self.pv.reset()
        self.sst.reset()
        self.vip.reset()
