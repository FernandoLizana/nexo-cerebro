"""Línea temporal fenomenológica compacta del event_log (Sprint 21)."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

_SALIENT_TYPES = (
    "action.selected",
    "language.produced",
    "metacognition.updated",
    "workspace.broadcast",
    "social.exchange",
    "behavior.snapshot",
)


def _event_label(ev: dict[str, Any]) -> str:
    etype = str(ev.get("type", ""))
    payload = ev.get("payload") or {}
    if etype == "action.selected":
        return f"action:{payload.get('action', '?')}"
    if etype == "language.produced":
        text = payload.get("text") or payload.get("utterance") or "..."
        return f"speech:{str(text)[:40]}"
    if etype == "metacognition.updated":
        return f"meta:{payload.get('felt', payload.get('clarity', '?'))}"
    if etype == "workspace.broadcast":
        return f"wm:{payload.get('content', payload.get('modality', '?'))}"
    if etype == "social.exchange":
        return f"social:{payload.get('kind', 'exchange')}"
    return etype


def build_phenomenology_timeline(
    events: list[dict[str, Any]],
    *,
    window_ticks: int = 15,
    max_segments: int = 80,
) -> dict[str, Any]:
    """Agrupa eventos salientes en ventanas temporales (no narrativa literal)."""
    salient = [ev for ev in events if ev.get("type") in _SALIENT_TYPES]
    if not salient:
        return {"n_segments": 0, "segments": [], "salient_events": 0}

    by_window: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for ev in salient:
        tick = int(ev.get("tick", 0))
        window = (tick // window_ticks) * window_ticks
        by_window[window].append(ev)

    segments: list[dict[str, Any]] = []
    for window_start in sorted(by_window.keys())[:max_segments]:
        window_events = by_window[window_start]
        labels = [_event_label(ev) for ev in window_events[:8]]
        segments.append(
            {
                "tick_start": window_start,
                "tick_end": window_start + window_ticks - 1,
                "n_events": len(window_events),
                "highlights": labels,
            }
        )
    return {
        "window_ticks": window_ticks,
        "salient_events": len(salient),
        "n_segments": len(segments),
        "segments": segments,
    }


def export_phenomenology(
    runtime: Any,
    path: Path,
    *,
    max_events: int = 2000,
    window_ticks: int = 15,
) -> dict[str, Any]:
    log = runtime.state_store.event_log[-max_events:]
    events = [
        {
            "tick": ev.tick,
            "type": ev.event_type,
            "source": ev.source,
            "payload": ev.payload,
        }
        for ev in log
    ]
    timeline = build_phenomenology_timeline(events, window_ticks=window_ticks)
    payload = {"timeline": timeline, "events_sampled": len(events)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "exported": True,
        "path": str(path),
        "n_segments": timeline["n_segments"],
        "salient_events": timeline["salient_events"],
    }
