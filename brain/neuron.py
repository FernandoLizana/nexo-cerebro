"""
Neurona Leaky Integrate-and-Fire con período refractario (más cercana a biología).
"""

from __future__ import annotations

import numpy as np


class LIFPopulation:
    __slots__ = (
        "n",
        "dt_ms",
        "tau_ms",
        "v_rest",
        "v_thresh",
        "v_reset",
        "refrac_ms",
        "v",
        "spikes",
        "_refrac_clock",
    )

    def __init__(
        self,
        n: int,
        *,
        dt_ms: float = 1.0,
        tau_ms: float = 20.0,
        v_rest: float = -70.0,
        v_thresh: float = -52.0,
        v_reset: float = -75.0,
        refrac_ms: int = 2,
    ) -> None:
        self.n = n
        self.dt_ms = dt_ms
        self.tau_ms = tau_ms
        self.v_rest = v_rest
        self.v_thresh = v_thresh
        self.v_reset = v_reset
        self.refrac_ms = max(0, int(refrac_ms))
        self.v = np.full(n, v_rest, dtype=np.float32)
        self.spikes = np.zeros(n, dtype=np.bool_)
        self._refrac_clock = np.zeros(n, dtype=np.int16)

    def reset(self) -> None:
        self.v.fill(self.v_rest)
        self.spikes.fill(False)
        self._refrac_clock.fill(0)

    def integrate(self, i_syn: np.ndarray, i_ext: np.ndarray) -> None:
        active = self._refrac_clock == 0
        dv = (
            (-(self.v - self.v_rest) + i_syn.astype(np.float32) + i_ext.astype(np.float32))
            * (self.dt_ms / self.tau_ms)
        )
        self.v = np.where(active, self.v + dv, self.v)
        fired = (self.v >= self.v_thresh) & active
        self.spikes = fired
        self.v[fired] = self.v_reset
        self._refrac_clock = np.maximum(self._refrac_clock - 1, 0)
        self._refrac_clock[fired] = self.refrac_ms

    @property
    def v_mean(self) -> float:
        return float(self.v.mean())
