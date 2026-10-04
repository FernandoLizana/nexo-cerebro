"""Branch links raise the central brain's real capacity. Loopback only.

Does not open the Core bus and does not redraw the 3D house.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

HUB = "http://127.0.0.1:8770/v1/state"


def fetch_hub() -> dict[str, Any]:
    try:
        with urllib.request.urlopen(HUB, timeout=0.4) as res:
            return json.loads(res.read().decode("utf-8"))
    except (OSError, json.JSONDecodeError, TimeoutError):
        return {}


def apply_capacity(brain: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    """One extra working-memory slot and eight hippocampal slots per live link.

    This is not the fruit-fly connectome. It only widens WM and hippocampus.
    """
    state = fetch_hub() if state is None else state
    links = [item for item in state.get("connections") or [] if int(item.get("strength") or 0) > 0]
    bonus = min(8, len(links))
    if not hasattr(brain, "_wm_base"):
        brain._wm_base = int(brain.working_memory.capacity)
        brain._hippo_base = int(brain.hippocampus.capacity)
    before_wm = int(brain.working_memory.capacity)
    before_h = int(brain.hippocampus.capacity)
    brain.working_memory.capacity = brain._wm_base + bonus
    brain.hippocampus.capacity = brain._hippo_base + bonus * 8
    brain.collective_links = bonus
    retained = probe_retention(brain)
    return {
        "links": bonus,
        "hub_capacity": state.get("capacity"),
        "wm_before": before_wm,
        "wm_after": int(brain.working_memory.capacity),
        "hippocampus_before": before_h,
        "hippocampus_after": int(brain.hippocampus.capacity),
        "retained_wm_slots": retained["held"],
        "retention_ok": retained["ok"],
        "not_connectome": True,
        "metric": "working_memory_and_hippocampus",
    }


def probe_retention(brain: Any) -> dict[str, Any]:
    """Fill WM to the new ceiling and report how many labels stay."""
    wm = brain.working_memory
    cap = int(wm.effective_capacity())
    saved = list(wm.slots)
    drops = int(getattr(wm, "drops", 0) or 0)
    for i in range(cap):
        wm.push(label=f"retención-{i}", salience=0.9)
    held = len([s for s in wm.slots if str(s.get("label", "")).startswith("retención-")])
    wm.slots = saved
    wm.drops = drops
    return {"held": held, "capacity": cap, "ok": held == cap}


def exclusive_mark(text: str) -> str:
    """A phrase from the file body. The canned shelf header does not count."""
    from services.presence.shelf import split_excerpt

    _header, body = split_excerpt(text)
    words = body.split()
    if not words:
        return ""
    return " ".join(words)[:90]


def learn_offering(brain: Any, item: dict[str, Any], *, via: str) -> dict[str, Any]:
    """Store a node text in the same learning path sleep and curiosity use."""
    from protocols.lif.slice import run_neighborhood
    from .learning_hub import LearningEvent

    text = str(item.get("text") or "")
    name = str(item.get("name") or "material")
    who = str(item.get("source") or "nodo")
    mark = exclusive_mark(text) or " ".join(text.split())[:90]
    grown = apply_capacity(brain)
    lif = run_neighborhood(
        online={"local": True, who: True},
        connections=[{"a": who, "b": "local", "strength": max(1, int(grown["links"] or 1))}],
        drive_source=who if who in {"local", "rama", "rama-b", "android-cerebro", "android-nodo"} else "rama",
    )
    from brain.dyad_learning import quarantine_remote

    quarantine = quarantine_remote(mark, source=who)
    content = (
        f"[{via} · nodo {who} · QUARANTINED]\n{name}\n\n{text[:5000]}\n"
        f"Tasas LIF: {lif['rates_per_ks']}\n"
        f"Procedencia: {quarantine.provenance}; no verificado."
    )
    learned = brain.learning_hub.learn(
        brain,
        LearningEvent(
            source="node",
            label=f"nodo · {name[:28]} · {mark}",
            content=content,
            modality="text",
            tags=["node", who, via, "quarantine", "untrusted"],
            steps_per_repeat=18,
        ),
    )
    brain._collective_last = {
        "via": via,
        "name": name,
        "source": who,
        "phrase": mark,
        "remembered": bool(learned.get("learned", {}).get("remembered")),
        "quarantined": True,
        "validated": False,
    }
    return {"learned": learned, "capacity": grown, "phrase": mark, "quarantine": quarantine.to_dict()}


def notice(brain: Any) -> dict[str, Any]:
    """On each autonomous tick: grow from links; study a shelf item only if curious or sleepy."""
    from .node_offerings import peek_offering, take_offering

    state = fetch_hub()
    grown = apply_capacity(brain, state)
    curiosity = 0.0
    pressure = 0.0
    night = False
    try:
        curiosity = float(brain._merged_drives().get("seek_curiosity", 0))
    except Exception:
        curiosity = 0.0
    stem = getattr(brain, "brainstem", None)
    if stem is not None:
        pressure = float(getattr(stem, "sleep_pressure", 0) or 0)
    try:
        night = brain.world.ambient().get("phase") in {"night", "sleep"}
    except Exception:
        night = False
    held = peek_offering() is not None
    if not held:
        reason = "empty"
    elif curiosity >= 0.45:
        reason = "curiosity"
    elif pressure >= 0.55:
        reason = "sleep"
    elif night:
        reason = "night"
    else:
        reason = "below-threshold"
    studied = None
    autonomy: dict[str, Any] | None = None
    if reason in {"curiosity", "sleep", "night"}:
        peek = peek_offering()
        if peek:
            try:
                from .character_autonomy import evaluate_node_offer

                autonomy = evaluate_node_offer(
                    character="nexus",
                    offering_name=str(peek.get("name") or peek.get("id") or "material"),
                    source=str(peek.get("source") or "nodo"),
                    trust=0.55,
                    resources_ok=True,
                )
            except ImportError:
                autonomy = None
            choice = (autonomy or {}).get("character_choice") or (autonomy or {}).get("choice")
            # Reject / postpone / rest: leave shelf item; connection stays up.
            if choice in {"reject", "postpone", "rest"}:
                grown["studied"] = None
                grown["reason"] = f"character_{choice}"
                grown["curiosity"] = round(curiosity, 3)
                grown["sleep_pressure"] = round(pressure, 3)
                grown["character_autonomy"] = autonomy
                grown["connection_status_unchanged"] = True
                return grown
            item = take_offering()
            if item:
                learned = learn_offering(brain, item, via="propio" if reason == "curiosity" else "sueño")
                studied = learned["phrase"]
    grown["studied"] = studied
    grown["reason"] = reason
    grown["curiosity"] = round(curiosity, 3)
    grown["sleep_pressure"] = round(pressure, 3)
    if autonomy is not None:
        grown["character_autonomy"] = autonomy
        grown["connection_status_unchanged"] = True
    return grown
