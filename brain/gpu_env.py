"""
Configuración CUDA / NVIDIA para laptops híbridas (Intel iGPU + RTX).

Debe ejecutarse antes de importar CuPy o `brain.backend`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _find_cuda_root() -> Path | None:
    env = os.environ.get("CUDA_PATH")
    if env:
        p = Path(env)
        if p.is_dir():
            return p
    if sys.platform != "win32":
        return None
    base = Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA")
    if not base.is_dir():
        return None
    versions = sorted(base.glob("v*"), reverse=True)
    return versions[0] if versions else None


def configure_cuda_env(*, force: bool = False) -> dict[str, str | bool]:
    """
    Fija variables para preferir la NVIDIA dedicada y permitir GPU en modo UI.

    Returns dict con flags útiles para /api/health.
    """
    status: dict[str, str | bool] = {"cuda_path_set": False, "cupy_ok": False}

    if force or os.environ.get("CEREBRO_USE_GPU") is None:
        os.environ.setdefault("CEREBRO_USE_GPU", "1")

    os.environ.setdefault("CUDA_DEVICE_ORDER", "PCI_BUS_ID")
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")

    cuda_root = _find_cuda_root()
    if cuda_root is not None:
        os.environ.setdefault("CUDA_PATH", str(cuda_root))
        bin_dir = cuda_root / "bin"
        if bin_dir.is_dir():
            path = os.environ.get("PATH", "")
            if str(bin_dir) not in path:
                os.environ["PATH"] = f"{bin_dir};{path}"
        status["cuda_path_set"] = True
        status["cuda_path"] = str(cuda_root)

    os.environ.setdefault("CEREBRO_GPU_MIN_STEPS", "6")
    os.environ.setdefault("CEREBRO_MIN_NEURONS_GPU", "400")
    os.environ.setdefault("CEREBRO_GPU_MAX_STEPS", "120")

    if os.environ.get("CEREBRO_USE_GPU", "").strip().lower() in ("1", "true", "yes"):
        try:
            import cupy as cp  # noqa: F401

            status["cupy_ok"] = True
        except ImportError:
            os.environ["CEREBRO_USE_GPU"] = "0"
            status["cupy_ok"] = False
        except Exception:
            status["cupy_ok"] = False

    return status
