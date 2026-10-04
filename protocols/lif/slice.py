"""Small neighborhood the nodes and the central can both run.

Nine units. Not the fruit-fly connectome.
0 nexo, 1 local, 2 rama, 3 rama-b, 4 cerebro, 5 nodo, 6-8 materials.
"""

from __future__ import annotations

from typing import Any

from protocols.lif.tier0 import run_lif

SOURCES = ("local", "rama", "rama-b", "android-cerebro", "android-nodo")


def run_neighborhood(
    *,
    online: dict[str, bool],
    connections: list[dict[str, Any]],
    drive_source: str | None = None,
    ticks: int = 40,
) -> dict[str, Any]:
    edges: list[tuple[int, int, int]] = []
    silence: list[int] = []
    for index, source in enumerate(SOURCES, start=1):
        if online.get(source):
            edges.append((index, 0, 4))
        else:
            silence.append(index)
    for link in connections:
        try:
            a = SOURCES.index(str(link.get("a"))) + 1
            b = SOURCES.index(str(link.get("b"))) + 1
        except ValueError:
            continue
        count = max(1, min(12, int(link.get("strength") or 1)))
        edges.append((a, b, count))
        edges.append((b, a, count))
    drive: list[int] = []
    material = len(SOURCES) + 1
    if drive_source in SOURCES:
        drive.append(SOURCES.index(drive_source) + 1)
        edges.append((SOURCES.index(drive_source) + 1, material, 6))
    result = run_lif(n=material + 3, edges=edges, ticks=ticks, drive=drive, silence=silence, drive_every=4)
    result["labels"] = ["nexo", *SOURCES, "m1", "m2", "m3"]
    return result
