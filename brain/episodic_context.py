"""
Contexto episódico multimodal: cuerpo + habitación + acción + percepción.

Los recuerdos humanos están anclados al estado interoceptivo y al lugar;
este módulo fusiona esas señales para codificar y recuperar engramas.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .encode import encode_text

CONTEXT_DIM = 32
RICH_EXTRA_DIM = 8
SENSORY_WEIGHT = 0.50
CONTEXT_WEIGHT = 0.35
ROOM_WEIGHT = 0.15


def _fit(vec: np.ndarray, n: int) -> np.ndarray:
    out = np.zeros(n, dtype=np.float32)
    v = np.asarray(vec, dtype=np.float32).ravel()
    if v.size == 0:
        return out
    if v.size >= n:
        out[:] = v[:n]
    else:
        out[: v.size] = v
    m = float(out.max())
    if m > 1e-6:
        out /= m
    return out


def encode_body_vector(body: dict[str, Any] | Any, dim: int = 12) -> np.ndarray:
    """Vector interoceptivo compacto."""
    if hasattr(body, "encode"):
        return np.asarray(body.encode(dim), dtype=np.float32)
    keys = ("hunger", "thirst", "body_temp", "fatigue", "comfort", "bladder")
    vec = np.zeros(dim, dtype=np.float32)
    for i, k in enumerate(keys):
        if i >= dim:
            break
        vec[i] = float(body.get(k, 0.0))
    if dim > 6:
        bt = float(body.get("body_temp", 0.5))
        if dim > 6:
            vec[6] = max(0.0, bt - 0.55)
        if dim > 7:
            vec[7] = max(0.0, 0.45 - bt)
    return vec


def encode_motor_vector(motor: list[int], *, dim: int = 12, n_motor: int = 72) -> np.ndarray:
    vec = np.zeros(dim, dtype=np.float32)
    for m in motor[:dim]:
        idx = int(m) % max(n_motor, 1)
        slot = idx % dim
        vec[slot] = max(vec[slot], 1.0 - 0.08 * (idx // dim))
    return vec


def build_rich_extras(
    *,
    olfaction: dict | None = None,
    affect: dict | None = None,
    posture: dict | None = None,
) -> np.ndarray:
    """Olfato + afecto + postura para contexto episódico rico."""
    vec = np.zeros(RICH_EXTRA_DIM, dtype=np.float32)
    if olfaction:
        vec[0] = float(olfaction.get("intensity", 0))
        vec[1] = float(olfaction.get("valence_hint", 0))
    if affect:
        vec[2] = float(affect.get("valence", 0))
        vec[3] = float(affect.get("arousal", 0))
    if posture:
        vec[4] = float(posture.get("equilibrium", 0.5))
        vec[5] = float(posture.get("signal", 0))
    return vec


def build_context_vector(
    *,
    body: dict[str, Any] | Any,
    room: str,
    motor: list[int] | None = None,
    n_motor: int = 72,
    olfaction: dict | None = None,
    affect: dict | None = None,
    posture: dict | None = None,
) -> np.ndarray:
    """32 dims base + 8 ricos si hay olfato/afecto/postura."""
    ctx = np.zeros(CONTEXT_DIM + RICH_EXTRA_DIM, dtype=np.float32)
    ctx[:12] = encode_body_vector(body, 12)
    room_bits = encode_text(room or "unknown", 8)
    ctx[12:20] = room_bits[:8]
    ctx[20:32] = encode_motor_vector(motor or [], dim=12, n_motor=n_motor)
    if olfaction or affect or posture:
        ctx[32:40] = build_rich_extras(olfaction=olfaction, affect=affect, posture=posture)
    return ctx[:CONTEXT_DIM] if not (olfaction or affect or posture) else ctx


def fuse_episodic_pattern(
    sensory: np.ndarray,
    *,
    n: int,
    body: dict[str, Any] | Any,
    room: str,
    motor: list[int] | None = None,
    n_motor: int = 72,
    olfaction: dict | None = None,
    affect: dict | None = None,
    posture: dict | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Fusiona percepción + contexto en un vector de tamaño n.
    Retorna (fused, context_vector).
    """
    ctx = build_context_vector(
        body=body,
        room=room,
        motor=motor,
        n_motor=n_motor,
        olfaction=olfaction,
        affect=affect,
        posture=posture,
    )
    ctx_slots = min(CONTEXT_DIM, max(8, n // 12))
    sensory_dims = n - ctx_slots

    fused = np.zeros(n, dtype=np.float32)
    s = np.asarray(sensory, dtype=np.float32).ravel()
    if s.size >= sensory_dims:
        fused[:sensory_dims] = s[:sensory_dims]
    else:
        fused[: s.size] = s
    fused[sensory_dims : sensory_dims + ctx.size] = ctx[:ctx_slots]
    m = float(fused.max())
    if m > 1e-6:
        fused /= m
    return np.clip(fused, 0.0, 1.0), ctx


def multimodal_similarity(
    query_sensory: np.ndarray,
    query_ctx: np.ndarray,
    query_room: str,
    mem_sensory: np.ndarray,
    mem_ctx: np.ndarray,
    mem_room: str,
) -> float:
    """Similitud ponderada: percepción + contexto corporal/situacional + habitación."""
    def cos(a: np.ndarray, b: np.ndarray) -> float:
        a = np.asarray(a, dtype=np.float32).ravel()
        b = np.asarray(b, dtype=np.float32).ravel()
        n = min(a.size, b.size)
        if n == 0:
            return 0.0
        if a.size != b.size:
            a, b = a[:n], b[:n]
        na = float(np.linalg.norm(a))
        nb = float(np.linalg.norm(b))
        if na < 1e-6 or nb < 1e-6:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    s_sens = cos(
        np.asarray(query_sensory, dtype=np.float32).ravel(),
        np.asarray(mem_sensory, dtype=np.float32).ravel(),
    )
    s_ctx = cos(
        np.asarray(query_ctx, dtype=np.float32).ravel(),
        np.asarray(mem_ctx, dtype=np.float32).ravel(),
    )
    s_room = 1.0 if (query_room or "") == (mem_room or "") else 0.0
    if not mem_room and not query_room:
        s_room = 0.5
    return SENSORY_WEIGHT * s_sens + CONTEXT_WEIGHT * s_ctx + ROOM_WEIGHT * s_room
