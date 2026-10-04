"""P8 Web Lab chaos scenario registry."""

from __future__ import annotations

from pathlib import Path

from nexo_qa.chaos.models import PerturbationSpec, TriggerSpec

REPO = Path(__file__).resolve().parents[2]
WEB_LAB = REPO / "tests" / "fixtures" / "web_lab" / "chaos"

SCENARIOS: dict[str, dict] = {
    "INTERRUPTION_FORM": {
        "html": "interruption_form.html",
        "perturbation": PerturbationSpec(
            perturbation_id="interruption_form",
            type="INTERRUPTION",
            trigger=TriggerSpec(kind="AFTER_ACTION", after_action_count=2),
            duration_ticks=3,
            parameters={"allowed_actions": ("wait",)},
        ),
    },
    "LATENCY_SUBMIT": {
        "html": "latency_submit.html",
        "perturbation": PerturbationSpec(
            perturbation_id="latency_submit",
            type="LATENCY",
            trigger=TriggerSpec(kind="AFTER_ACTION", after_action_count=1),
            duration_ticks=2,
            parameters={"delay_ticks": 2},
        ),
    },
    "TRANSIENT_ERROR_RETRY": {
        "html": "transient_error.html",
        "perturbation": PerturbationSpec(
            perturbation_id="transient_error",
            type="TRANSIENT_ERROR",
            trigger=TriggerSpec(kind="AT_TICK", at_tick=1),
            duration_ticks=5,
            parameters={"fail_attempts": 1},
        ),
    },
    "SESSION_EXPIRY": {
        "html": "session_expiry.html",
        "perturbation": PerturbationSpec(
            perturbation_id="session_expiry",
            type="SESSION_EXPIRY",
            trigger=TriggerSpec(kind="AFTER_ACTION", after_action_count=2),
            duration_ticks=4,
        ),
    },
    "LAYOUT_SHIFT": {
        "html": "layout_shift.html",
        "perturbation": PerturbationSpec(
            perturbation_id="layout_shift",
            type="VISUAL_CHANGE",
            trigger=TriggerSpec(kind="AFTER_ACTION", after_action_count=1),
            duration_ticks=6,
        ),
    },
    "MODAL_DISTRACTION": {
        "html": "modal_distraction.html",
        "perturbation": PerturbationSpec(
            perturbation_id="modal_distraction",
            type="MODAL_DISTRACTION",
            trigger=TriggerSpec(kind="AT_TICK", at_tick=0),
            duration_ticks=4,
        ),
    },
    "FEEDBACK_DELAY": {
        "html": "feedback_delay.html",
        "perturbation": PerturbationSpec(
            perturbation_id="feedback_delay",
            type="FEEDBACK_DELAY",
            trigger=TriggerSpec(kind="AFTER_ACTION", after_action_count=1),
            duration_ticks=2,
            parameters={"delay_ticks": 2},
        ),
    },
    "DISABLED_CONTROL": {
        "html": "disabled_control.html",
        "perturbation": PerturbationSpec(
            perturbation_id="disabled_control",
            type="CONTROL_DISABLE",
            trigger=TriggerSpec(kind="AT_TICK", at_tick=0),
            duration_ticks=3,
            parameters={"disabled_actions": ("activate_switch",)},
        ),
    },
}


def scenario_html_path(scenario_id: str) -> Path:
    meta = SCENARIOS[scenario_id]
    return WEB_LAB / str(meta["html"])


def list_scenarios() -> tuple[str, ...]:
    return tuple(SCENARIOS.keys())
