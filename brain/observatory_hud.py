"""
HUD observatorio completo — item 99.

Telemetría, causal, TD, WM, atención y tracks de estudio en un solo panel.
Solo lectura: no selecciona acciones.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .causal_hud import build_causal_hud
from .experiment_flags import get_flags
from .language_dynamics import study_tracks_snapshot

if TYPE_CHECKING:
    from .mind import InfantApeBrain


def build_observatory_hud(brain: InfantApeBrain) -> dict[str, Any]:
    flags = get_flags(brain)
    causal = build_causal_hud(brain)
    telemetry = brain.neural_telemetry.to_dict() if hasattr(brain, "neural_telemetry") else {}
    td = brain.td_reward.to_dict() if hasattr(brain, "td_reward") else {}
    if flags.enable_reward_learning and hasattr(brain, "reward_learning"):
        td = {**td, "reward_stack": brain.reward_learning.to_dict()}
    wm = brain.working_memory.to_dict() if hasattr(brain, "working_memory") else {}
    attention = {}
    if hasattr(brain, "cognition") and hasattr(brain.cognition, "attention_budget"):
        attention = brain.cognition.attention_budget.to_dict()
    tracks = study_tracks_snapshot(brain)
    track_progress = {
        k: round(float((v or {}).get("progress", 0) or 0), 3)
        for k, v in tracks.items()
        if isinstance(v, dict)
    }
    top_track = ""
    if track_progress:
        top_track = max(track_progress.items(), key=lambda item: item[1])[0]

    agency_guard = {
        **dict(causal.get("agency_guard") or {}),
        "observatory_selects_actions": False,
        "sleep_selects_actions": False,
        "grounding_selects_actions": False,
        "tutor_selects_actions": False,
        "deliberation_selects_actions": True,
    }

    return {
        "causal": causal,
        "telemetry": telemetry,
        "td": td,
        "working_memory": wm,
        "attention": attention,
        "study_tracks": tracks,
        "track_progress": track_progress,
        "top_study_track": top_track,
        "agency_guard": agency_guard,
        "one_liner": (
            f"{causal.get('top_drive') or '—'} → {causal.get('choice_key') or '—'} · "
            f"TD δ={round(float(td.get('last_delta', 0)), 3)} · "
            f"WM {wm.get('load', 0):.0%} · att {attention.get('used', 0)}/{attention.get('budget', 0)} · "
            f"track {top_track or '—'}"
        ),
    }
