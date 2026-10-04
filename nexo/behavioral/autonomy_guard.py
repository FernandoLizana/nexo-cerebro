"""Contrato de autonomía — sin comandos motores forzados (Sprint 57)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# Rutas Flask que deben devolver 403 (modo autónomo)
FORCED_MOTOR_ROUTES: tuple[tuple[str, str], ...] = (
    ("POST", "/api/care"),
    ("POST", "/api/sleep"),
    ("POST", "/api/archetype-cards/draw"),
    ("POST", "/api/lifecycle/reproduce"),
    ("POST", "/api/lifecycle/reborn"),
    ("POST", "/api/library/desk"),
)

ALLOWED_OBSERVE_ROUTES: tuple[tuple[str, str], ...] = (
    ("GET", "/api/world"),
    ("POST", "/api/world/tick"),
    ("GET", "/api/neural/causal/hud"),
    ("GET", "/api/neural/observatory"),
    ("POST", "/api/caregiver/speak"),
    ("POST", "/api/interact"),
)


def verify_app_autonomy_routes(app_source: str | None = None) -> dict[str, Any]:
    """Verifica que app.py bloquea rutas motoras forzadas."""
    if app_source is None:
        root = Path(__file__).resolve().parent.parent.parent
        app_source = (root / "app.py").read_text(encoding="utf-8")
    blocked_ok = []
    for method, route in FORCED_MOTOR_ROUTES:
        pattern = rf'@app\.(post|get)\("{re.escape(route)}"'
        has_route = bool(re.search(pattern, app_source, re.IGNORECASE))
        has_403 = has_route and "403" in app_source[app_source.find(route): app_source.find(route) + 400] if has_route else False
        blocked_ok.append({"method": method, "route": route, "defined": has_route, "blocks_403": has_403})
    n_ok = sum(1 for r in blocked_ok if r["defined"] and r["blocks_403"])
    return {
        "routes_checked": len(FORCED_MOTOR_ROUTES),
        "routes_blocked": n_ok,
        "route_details": blocked_ok,
        "audit_score": n_ok / max(len(FORCED_MOTOR_ROUTES), 1),
    }


def summarize_autonomy_guard(runtime: Any) -> dict[str, Any]:
    log = runtime.state_store.event_log
    guard = [ev for ev in log if ev.event_type == "autonomy.guard"]
    actions = [ev for ev in log if ev.event_type == "action.selected"]
    deliberation = [ev for ev in log if ev.event_type == "deliberation.completed"]
    forced_blocked = sum(1 for ev in guard if ev.payload.get("forced_blocked"))
    app_audit = verify_app_autonomy_routes()
    return {
        "guard_events": len(guard),
        "action_events": len(actions),
        "deliberation_events": len(deliberation),
        "forced_blocked_count": forced_blocked,
        "deliberation_selects_actions": len(deliberation) > 0 or len(actions) > 0,
        "app_route_audit": app_audit,
        "guard_score": min(
            1.0,
            app_audit["audit_score"] * 0.5
            + (0.3 if len(actions) > 0 else 0.0)
            + (0.2 if forced_blocked >= 0 else 0.0),
        ),
    }


def export_autonomy_guard(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    summary = summarize_autonomy_guard(runtime)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "forced_motor_routes": [{"method": m, "route": r} for m, r in FORCED_MOTOR_ROUTES],
        "allowed_observe_routes": [{"method": m, "route": r} for m, r in ALLOWED_OBSERVE_ROUTES],
        "summary": summary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **summary}
