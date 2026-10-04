"""Utilidades de enrutamiento para lesiones connectome."""

from __future__ import annotations

import numpy as np

from nexo.connectome.routing import ConnectomeRouter


def route_gain(
    router: ConnectomeRouter,
    source: str,
    target: str,
    signal: tuple[float, ...] | np.ndarray,
    *,
    salience: float = 1.0,
) -> float:
    """Ganancia efectiva normalizada de una arista (0 = severada o aún no entregada)."""
    delivered = router.latency_buffer.get_delivered(source, target)
    if delivered is not None and float(np.linalg.norm(delivered)) > 0.0:
        out = delivered
    else:
        out = router.route(source, target, signal, salience)
    vec = np.asarray(signal, dtype=np.float64)
    if vec.size == 0:
        vec = np.array([0.1], dtype=np.float64)
    in_norm = float(np.linalg.norm(vec))
    out_norm = float(np.linalg.norm(out))
    if in_norm < 1e-9:
        return 0.0 if out_norm < 1e-9 else 1.0
    return min(1.0, out_norm / in_norm)
