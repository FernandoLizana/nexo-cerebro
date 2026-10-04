"""
Sinapsis dispersas con plasticidad hebbiana y decaimiento sináptico.

Propagación vectorizada (SciPy CSR); GPU opcional vía backend.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse as sp

from .backend import get_backend


class SparseSynapses:
    """Matriz de pesos dispersa (CSR) para bajo uso de memoria."""

    __slots__ = (
        "n_pre",
        "n_post",
        "w",
        "indices",
        "indptr",
        "eta",
        "w_max",
        "trace_pre",
        "trace_post",
        "trace_decay",
        "_csr",
        "_csr_gpu",
    )

    def __init__(
        self,
        n_pre: int,
        n_post: int,
        *,
        density: float = 0.05,
        w_init: float = 0.85,
        eta: float = 0.004,
        w_max: float = 2.0,
        trace_decay: float = 0.95,
        rng: np.random.Generator | None = None,
    ) -> None:
        self.n_pre = n_pre
        self.n_post = n_post
        self.eta = eta
        self.w_max = w_max
        self.trace_decay = trace_decay
        self.trace_pre = np.zeros(n_pre, dtype=np.float32)
        self.trace_post = np.zeros(n_post, dtype=np.float32)
        self._csr_gpu = None

        rng = rng or np.random.default_rng(42)
        mask = rng.random((n_pre, n_post)) < density
        signs = np.where(rng.random((n_pre, n_post)) < 0.2, -1.0, 1.0)
        dense = (mask * signs * w_init * rng.uniform(0.5, 1.0, (n_pre, n_post))).astype(
            np.float32
        )
        self._build_csr(dense)

    def _build_csr(self, dense: np.ndarray) -> None:
        rows, cols = np.nonzero(dense)
        self.w = dense[rows, cols].astype(np.float32)
        self.indices = cols.astype(np.int32)
        counts = np.bincount(rows, minlength=self.n_pre)
        self.indptr = np.zeros(self.n_pre + 1, dtype=np.int32)
        self.indptr[1:] = np.cumsum(counts)
        self._csr = sp.csr_matrix(
            (self.w, self.indices, self.indptr), shape=(self.n_pre, self.n_post)
        )
        self._csr_gpu = get_backend().to_gpu_csr(self._csr)

    def _sync_csr_weights(self) -> None:
        self._csr.data = self.w
        if self._csr_gpu is not None:
            try:
                self._csr_gpu.data = get_backend()._cp.asarray(self.w)  # type: ignore
            except Exception:
                self._csr_gpu = get_backend().to_gpu_csr(self._csr)

    def forward(self, pre_spikes: np.ndarray) -> np.ndarray:
        pre = np.asarray(pre_spikes).astype(np.float32).ravel()
        be = get_backend()
        return be.spmv(self._csr, pre, self._csr_gpu)

    def hebbian_update(self, pre_spikes: np.ndarray, post_spikes: np.ndarray) -> None:
        self.trace_pre *= self.trace_decay
        self.trace_post *= self.trace_decay
        self.trace_pre[pre_spikes] = 1.0
        self.trace_post[post_spikes] = 1.0

        active_pre = np.flatnonzero(pre_spikes)
        active_post = set(np.flatnonzero(post_spikes))

        for pre in active_pre:
            start = self.indptr[pre]
            end = self.indptr[pre + 1]
            for k in range(start, end):
                post = self.indices[k]
                dw = self.eta * (
                    self.trace_pre[pre] * float(post in active_post)
                    + self.trace_post[post] * float(pre_spikes[pre])
                )
                self.w[k] = np.clip(self.w[k] + dw, -self.w_max, self.w_max)
        self._sync_csr_weights()

    def plasticity_step(
        self,
        pre_spikes: np.ndarray,
        post_spikes: np.ndarray,
        *,
        eta_scale: float = 1.0,
        use_stdp: bool = False,
    ) -> None:
        if use_stdp:
            self.stdp_update(pre_spikes, post_spikes, eta_scale=eta_scale)
        else:
            old = self.eta
            self.eta = min(self.eta * eta_scale, 0.05)
            self.hebbian_update(pre_spikes, post_spikes)
            self.eta = old

    def stdp_update(
        self,
        pre_spikes: np.ndarray,
        post_spikes: np.ndarray,
        *,
        eta_scale: float = 1.0,
    ) -> None:
        self.trace_pre *= self.trace_decay
        self.trace_post *= self.trace_decay
        self.trace_pre[pre_spikes] = 1.0
        self.trace_post[post_spikes] = 1.0
        active_pre = np.flatnonzero(pre_spikes)
        active_post = set(np.flatnonzero(post_spikes))
        eta = self.eta * eta_scale
        for pre in active_pre:
            start, end = self.indptr[pre], self.indptr[pre + 1]
            for k in range(start, end):
                post = self.indices[k]
                ltp = eta * self.trace_pre[pre] * float(post in active_post)
                ltd = 0.35 * eta * self.trace_post[post] * float(pre_spikes[pre])
                self.w[k] = np.clip(self.w[k] + ltp - ltd, -self.w_max, self.w_max)
        self._sync_csr_weights()

    def homeostatic_scale(self, target_rate: float = 0.08) -> None:
        mean_w = float(np.abs(self.w).mean()) if self.w.size else 0.0
        if mean_w < 1e-6:
            return
        scale = float(np.clip(target_rate / mean_w, 0.85, 1.15))
        self.w *= scale
        self._sync_csr_weights()

    def soft_prune_weak(self, *, threshold: float = 0.02, rate: float = 0.01) -> int:
        """Poda suave de pesos |w| bajo umbral (adulto/anciano). Devuelve cuántos se anularon."""
        if self.w.size == 0 or rate <= 0:
            return 0
        mask = np.abs(self.w) < threshold
        n = int(mask.sum())
        if n == 0:
            return 0
        rng = np.random.default_rng(n + int(self.w.size))
        pick = rng.random(n) < rate
        idx = np.flatnonzero(mask)[pick]
        self.w[idx] = 0.0
        self._sync_csr_weights()
        return int(idx.size)

    def enable_gpu_matrices(self) -> None:
        self._csr_gpu = get_backend().to_gpu_csr(self._csr)
