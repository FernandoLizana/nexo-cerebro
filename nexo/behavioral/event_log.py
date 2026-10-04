"""Export compacto del event_log integrado."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def summarize_event_log_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Resumen fenomenológico compacto por tipo y fuente de evento."""
    events = payload.get("events") or []
    type_counts = Counter(str(ev.get("type", "")) for ev in events if ev.get("type"))
    source_counts = Counter(str(ev.get("source", "")) for ev in events if ev.get("source"))
    ticks = [int(ev["tick"]) for ev in events if isinstance(ev.get("tick"), int)]
    return {
        "n_events": len(events),
        "type_counts": dict(type_counts.most_common(20)),
        "source_counts": dict(source_counts.most_common(10)),
        "tick_min": min(ticks) if ticks else None,
        "tick_max": max(ticks) if ticks else None,
    }


def export_event_log(
    runtime: Any,
    path: Path,
    *,
    max_events: int = 2000,
) -> dict[str, Any]:
    """Serializa eventos recientes del runtime (no fenomenológico)."""
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
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"n_events": len(events), "events": events}
    summary = summarize_event_log_payload(payload)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "exported": True,
        "path": str(path),
        "n_events": len(events),
        "summary": summary,
    }
