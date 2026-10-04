"""Integer leaky integrate-and-fire. Same arithmetic in Python and Kotlin.

Units are 0.1 mV and 1 ms. Division truncates toward zero.
Silence zeros outgoing weights only, matching the fly model's code, not its README.
Poisson noise is not portable, so drive is a fixed kick every `drive_every` ms.
"""

from __future__ import annotations

from typing import Any

ENGINE_ID = "nexo-lif-tier0-v1"
MAX_UNITS = 32
MAX_TICKS = 200
MAX_EDGES = 128
V0 = -520
VRST = -520
VTH = -450
TM = 20
TAU = 5
DELAY = 2
RFC = 2
# Free parameter, scaled so a short node graph can cross threshold.
# The fly paper uses 0.275 mV because each edge already carries a large synapse count.
W_SYN = 80
DRIVE_KICK = 688


def trunc_div(num: int, den: int) -> int:
    if den == 0:
        return 0
    if num < 0:
        return -((-num) // den)
    return num // den


def run_lif(
    *,
    n: int,
    edges: list[tuple[int, int, int]],
    ticks: int,
    drive: list[int] | None = None,
    silence: list[int] | None = None,
    drive_every: int = 4,
) -> dict[str, Any]:
    if n < 1 or n > MAX_UNITS:
        raise ValueError(f"n must be 1..{MAX_UNITS}")
    if ticks < 1 or ticks > MAX_TICKS:
        raise ValueError(f"ticks must be 1..{MAX_TICKS}")
    if drive_every < 1:
        raise ValueError("drive_every must be >= 1")
    clean: list[tuple[int, int, int]] = []
    for pre, post, count in edges[:MAX_EDGES]:
        pre_i, post_i, count_i = int(pre), int(post), int(count)
        if pre_i < 0 or post_i < 0 or pre_i >= n or post_i >= n or pre_i == post_i:
            continue
        count_i = max(-12, min(12, count_i))
        if count_i == 0:
            continue
        clean.append((pre_i, post_i, count_i))
    drive_set = {int(i) for i in (drive or []) if 0 <= int(i) < n}
    silent = {int(i) for i in (silence or []) if 0 <= int(i) < n}
    v = [V0] * n
    g = [0] * n
    rfc = [0] * n
    spikes: list[str] = []
    counts = [0] * n
    due: list[tuple[int, int, int]] = []
    for tick in range(1, ticks + 1):
        if due:
            kept: list[tuple[int, int, int]] = []
            for when, post, delta in due:
                if when == tick:
                    g[post] += delta
                elif when > tick:
                    kept.append((when, post, delta))
            due = kept
        for i in range(n):
            if rfc[i] > 0:
                rfc[i] -= 1
                continue
            if i in drive_set and tick % drive_every == 0:
                v[i] += DRIVE_KICK
            g[i] -= trunc_div(g[i], TAU)
            v[i] += trunc_div(V0 - v[i] + g[i], TM)
            if v[i] > VTH:
                spikes.append(f"{tick}:{i}")
                counts[i] += 1
                v[i] = VRST
                g[i] = 0
                rfc[i] = RFC
                if i not in silent:
                    for pre, post, count in clean:
                        if pre == i:
                            due.append((tick + DELAY, post, count * W_SYN))
    rates = [counts[i] * 1000 // ticks for i in range(n)]
    return {
        "engine": ENGINE_ID,
        "spikes": spikes,
        "rates_per_ks": rates,
        "spike_count": len(spikes),
        "ticks": ticks,
        "n": n,
    }


def golden_slice() -> dict[str, Any]:
    """Fixed four-unit graph used by the Python and Kotlin tests."""
    return run_lif(
        n=4,
        edges=[(0, 1, 12), (1, 2, 12), (2, 3, 12)],
        ticks=40,
        drive=[0],
        silence=[],
        drive_every=4,
    )
