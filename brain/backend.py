"""
Backend de cómputo: CPU (NumPy/SciPy) por defecto; GPU opcional y acotada.

Variables de entorno (leídas en runtime, no solo al importar):
  CEREBRO_USE_GPU=1
  CEREBRO_GPU_MAX_STEPS=999999
  CEREBRO_GPU_PERSIST=1
  CEREBRO_GPU_AGGRESSIVE=1
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

import numpy as np


def _env_flag(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError:
        return default


@dataclass
class ComputeBackend:
    """Controla uso de GPU para no saturar la tarjeta."""

    gpu_requested: bool = False
    gpu_available: bool = False
    gpu_name: str = ""
    max_gpu_steps: int = 120
    min_neurons: int = 500
    _gpu_steps_this_episode: int = 0
    _last_gpu_release: float = 0.0
    _active_gpu_forward: bool = False
    _cp: object | None = None
    _pre_gpu_cache: dict[int, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.gpu_requested = _env_flag("CEREBRO_USE_GPU")
        self.max_gpu_steps = _env_int("CEREBRO_GPU_MAX_STEPS", 120)
        self.min_neurons = _env_int("CEREBRO_MIN_NEURONS_GPU", 500)
        if not self.gpu_requested:
            return
        try:
            import cupy as cp

            if cp.cuda.runtime.getDeviceCount() < 1:
                return
            a = cp.zeros(1, dtype=cp.float32)
            del a
            cp.get_default_memory_pool().free_all_blocks()
            self._cp = cp
            self.gpu_available = True
            props = cp.cuda.runtime.getDeviceProperties(0)
            self.gpu_name = props["name"].decode("utf-8", errors="replace")
        except Exception:
            self.gpu_available = False
            self._cp = None

    @property
    def label(self) -> str:
        if self.gpu_available:
            return f"GPU ({self.gpu_name})"
        if self.gpu_requested:
            return "GPU solicitada (no disponible, usando CPU)"
        return "CPU"

    def _min_steps_gpu(self) -> int:
        if _env_flag("CEREBRO_GPU_AGGRESSIVE"):
            return _env_int("CEREBRO_GPU_MIN_STEPS", 4)
        return _env_int("CEREBRO_GPU_MIN_STEPS", 6)

    def _gpu_cooldown_s(self) -> float:
        if _env_flag("CEREBRO_GPU_AGGRESSIVE"):
            return _env_float("CEREBRO_GPU_COOLDOWN", 0.0)
        return _env_float("CEREBRO_GPU_COOLDOWN", 0.15)

    def want_gpu_for_episode(self, n_neurons: int, total_steps: int) -> bool:
        if not self.gpu_available or n_neurons < self.min_neurons:
            return False
        if total_steps < self._min_steps_gpu():
            return False
        if time.monotonic() - self._last_gpu_release < self._gpu_cooldown_s():
            return False
        return True

    def begin_episode(self) -> None:
        self._gpu_steps_this_episode = 0
        self._active_gpu_forward = False

    def set_active_gpu(self, active: bool) -> None:
        self._active_gpu_forward = active and self.gpu_available

    def gpu_steps_budget(self, total_steps: int) -> int:
        if not self.gpu_available:
            return 0
        return min(total_steps, self.max_gpu_steps, self.max_gpu_steps - self._gpu_steps_this_episode)

    def record_gpu_steps(self, n: int) -> None:
        self._gpu_steps_this_episode += n

    def release_gpu(self, *, force: bool = False) -> None:
        if not force and _env_flag("CEREBRO_GPU_PERSIST"):
            return
        if self._cp is not None:
            try:
                self._cp.get_default_memory_pool().free_all_blocks()
                self._cp.get_default_pinned_memory_pool().free_all_blocks()
            except Exception:
                pass
        self._pre_gpu_cache.clear()
        self._last_gpu_release = time.monotonic()

    def to_gpu_csr(self, scipy_csr):
        if not self.gpu_available or self._cp is None:
            return None
        try:
            from cupyx.scipy import sparse as csparse

            return csparse.csr_matrix(scipy_csr)
        except Exception:
            return None

    def gpu_diagnostics(self, *, n_neurons: int = 0, episode_steps: int = 0) -> dict:
        reasons: list[str] = []
        if not self.gpu_requested:
            reasons.append("CEREBRO_USE_GPU no activo")
        elif not self.gpu_available:
            reasons.append("CuPy/CUDA no disponible")
        else:
            if n_neurons < self.min_neurons:
                reasons.append(f"neuronas {n_neurons} < mínimo {self.min_neurons}")
            if episode_steps < self._min_steps_gpu():
                reasons.append(
                    f"pasos {episode_steps} < mínimo GPU {self._min_steps_gpu()}"
                )
        will_use = self.want_gpu_for_episode(n_neurons, episode_steps) if episode_steps else False
        return {
            "gpu_requested": self.gpu_requested,
            "gpu_available": self.gpu_available,
            "gpu_name": self.gpu_name,
            "label": self.label,
            "min_neurons": self.min_neurons,
            "min_steps_gpu": self._min_steps_gpu(),
            "max_gpu_steps": self.max_gpu_steps,
            "will_use_for_episode": will_use,
            "reasons_if_not": reasons if not will_use else [],
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        }

    def spmv(self, scipy_csr, pre: np.ndarray, gpu_csr=None) -> np.ndarray:
        pre_f = np.asarray(pre, dtype=np.float32).ravel()
        if (
            self._active_gpu_forward
            and gpu_csr is not None
            and self._cp is not None
            and self._gpu_steps_this_episode < self.max_gpu_steps
        ):
            cp = self._cp
            x = cp.asarray(pre_f)
            y = x @ gpu_csr
            return cp.asnumpy(y).astype(np.float32, copy=False)
        out = pre_f @ scipy_csr
        return np.asarray(out, dtype=np.float32).ravel()


_backend: ComputeBackend | None = None


def get_backend() -> ComputeBackend:
    global _backend
    if _backend is None:
        _backend = ComputeBackend()
    return _backend


def reset_backend() -> ComputeBackend:
    """Reinicia el singleton (p. ej. tras cambiar CEREBRO_USE_GPU en experiments)."""
    global _backend
    if _backend is not None:
        _backend.release_gpu(force=True)
    _backend = None
    return get_backend()
