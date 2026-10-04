"""Activa GPU NVIDIA para experimentos batch (RTX / CuPy)."""

from __future__ import annotations

import os

from brain.backend import reset_backend


def enable_experiment_gpu() -> bool:
    os.environ["CEREBRO_USE_GPU"] = "1"
    os.environ["CEREBRO_GPU_AGGRESSIVE"] = "1"
    os.environ["CEREBRO_GPU_PERSIST"] = "1"
    os.environ["CEREBRO_GPU_MAX_STEPS"] = "999999"
    os.environ["CEREBRO_MIN_NEURONS_GPU"] = "200"
    os.environ["CEREBRO_GPU_MIN_STEPS"] = "4"
    os.environ["CEREBRO_GPU_COOLDOWN"] = "0"
    backend = reset_backend()
    return backend.gpu_available


def release_experiment_gpu() -> None:
    from brain.backend import get_backend

    os.environ.pop("CEREBRO_GPU_PERSIST", None)
    get_backend().release_gpu(force=True)


def gpu_label() -> str:
    from brain.backend import get_backend

    return get_backend().label
