"""
Columna laminar simplificada (L4→L2/3→L5 + L6 feedback).

Modelo mesoscale: no sustituye la corteza principal; modula asociativa y motora.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .neuron import LIFPopulation
from .synapse import SparseSynapses


@dataclass
class LaminarAssociativeStack:
    """
    Cuatro capas corticales acopladas a la red asociativa principal.

    L4: entrada talámica (sensorial)
    L2/3: integración intracortical
    L5: salida motora/cortical profunda
    L6: feedback modulatorio a L4
    """

    n_per_layer: int = 16
    density: float = 0.12
    l4: LIFPopulation = field(init=False)
    l23: LIFPopulation = field(init=False)
    l5: LIFPopulation = field(init=False)
    l6: LIFPopulation = field(init=False)
    s_to_l4: SparseSynapses = field(init=False)
    l4_to_l23: SparseSynapses = field(init=False)
    l23_to_l5: SparseSynapses = field(init=False)
    l6_to_l4: SparseSynapses = field(init=False)
    last: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        n = max(4, int(self.n_per_layer))
        self.n_per_layer = n
        ref = 2
        self.l4 = LIFPopulation(n, tau_ms=11.0, v_thresh=-54.0, refrac_ms=ref)
        self.l23 = LIFPopulation(n, tau_ms=18.0, v_thresh=-53.0, refrac_ms=ref)
        self.l5 = LIFPopulation(n, tau_ms=22.0, v_thresh=-52.5, refrac_ms=ref)
        self.l6 = LIFPopulation(n, tau_ms=26.0, v_thresh=-53.5, refrac_ms=ref)
        rng = np.random.default_rng(47)
        d = self.density
        eta = 0.0025
        in_w = max(8, n * 2)
        self.s_to_l4 = SparseSynapses(in_w, n, density=d * 1.1, rng=rng, eta=eta)
        self.l4_to_l23 = SparseSynapses(n, n, density=d, rng=rng, eta=eta)
        self.l23_to_l5 = SparseSynapses(n, n, density=d * 0.9, rng=rng, eta=eta)
        self.l6_to_l4 = SparseSynapses(n, n, density=d * 0.55, rng=rng, eta=eta)

    @property
    def n_neurons(self) -> int:
        return 4 * self.n_per_layer

    def reset(self) -> None:
        for pop in (self.l4, self.l23, self.l5, self.l6):
            pop.reset()

    def step(
        self,
        sensory: np.ndarray,
        *,
        gain: float,
        gamma_amp: float = 1.0,
        n_assoc: int,
        n_motor: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        s = np.asarray(sensory, dtype=np.float32).ravel()
        in_n = self.s_to_l4.n_pre
        if s.size < in_n:
            s = np.pad(s, (0, in_n - s.size))
        pre = (s[:in_n] > 0.15).astype(np.bool_)

        z = np.zeros(self.n_per_layer, dtype=np.float32)
        g = float(gain) * float(gamma_amp)

        i_l4 = self.s_to_l4.forward(pre) * g + self.l6_to_l4.forward(self.l6.spikes) * g * 0.35
        self.l4.integrate(z, i_l4)

        i_l23 = self.l4_to_l23.forward(self.l4.spikes) * g
        self.l23.integrate(i_l23, z)

        i_l5 = self.l23_to_l5.forward(self.l23.spikes) * g * 1.05
        self.l5.integrate(i_l5, z)

        # L6: feedback desde actividad L5 (cortico-talámico simplificado)
        l5_act = np.clip(self.l5.v / max(float(np.abs(self.l5.v).max()), 1e-5), 0, 1)
        self.l6.integrate(l5_act * 8.0, z)

        assoc_boost = np.zeros(max(1, n_assoc), dtype=np.float32)
        motor_boost = np.zeros(max(1, n_motor), dtype=np.float32)
        l23_n = min(n_assoc, self.n_per_layer)
        l5_n = min(n_motor, self.n_per_layer)
        assoc_boost[:l23_n] = np.clip(self.l23.v[:l23_n] / 40.0, 0, 0.35)
        motor_boost[:l5_n] = np.clip(self.l5.v[:l5_n] / 35.0, 0, 0.4)

        self.last = {
            "l4": round(float(self.l4.spikes.mean()), 3),
            "l23": round(float(self.l23.spikes.mean()), 3),
            "l5": round(float(self.l5.spikes.mean()), 3),
            "l6": round(float(self.l6.spikes.mean()), 3),
        }
        return assoc_boost, motor_boost

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_per_layer": self.n_per_layer,
            "n_neurons": self.n_neurons,
            "layers": dict(self.last),
        }
