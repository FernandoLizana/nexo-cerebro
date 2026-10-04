"""Flask app factory — read-only local dashboard."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

from services.dashboard.auth import DashboardAuthError, LocalDashboardAuth
from services.dashboard.telemetry import FORBIDDEN_CONTROL_ACTIONS, TelemetryHub

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def create_app(
    *,
    auth: LocalDashboardAuth | None = None,
    hub: TelemetryHub | None = None,
) -> Flask:
    app = Flask(__name__, template_folder=str(_TEMPLATE_DIR))
    app.config["NEXO_DASHBOARD_AUTH"] = auth or LocalDashboardAuth()
    app.config["NEXO_TELEMETRY_HUB"] = hub or TelemetryHub()
    app.config["NEXO_DASHBOARD_READ_ONLY"] = True

    def _require_auth() -> None:
        token = request.headers.get(LocalDashboardAuth.HEADER) or request.args.get("token")
        app.config["NEXO_DASHBOARD_AUTH"].check(token)

    @app.get("/")
    def index() -> str:
        # Page shell is public on loopback; API calls still need token.
        return render_template("dashboard.html")

    @app.get("/api/health")
    def health() -> Response:
        return jsonify(
            {
                "ok": True,
                "read_only": True,
                "job_injection_enabled": False,
            }
        )

    @app.get("/api/overview")
    def overview() -> Response | tuple[Response, int]:
        try:
            _require_auth()
        except DashboardAuthError as exc:
            return jsonify({"error": str(exc)}), 401
        hub_obj: TelemetryHub = app.config["NEXO_TELEMETRY_HUB"]
        return jsonify(hub_obj.overview())

    @app.get("/api/graph")
    def graph() -> Response | tuple[Response, int]:
        try:
            _require_auth()
        except DashboardAuthError as exc:
            return jsonify({"error": str(exc)}), 401
        hub_obj: TelemetryHub = app.config["NEXO_TELEMETRY_HUB"]
        return jsonify(hub_obj.graph())

    # Explicit deny surface for control-plane probes
    @app.route("/api/jobs", methods=["GET", "POST", "PUT", "DELETE"])
    @app.route("/api/dispatch", methods=["GET", "POST"])
    @app.route("/api/execute", methods=["GET", "POST"])
    @app.route("/api/shell", methods=["GET", "POST"])
    def reject_control() -> tuple[Response, int]:
        return (
            jsonify(
                {
                    "error": "control plane disabled on dashboard",
                    "read_only": True,
                    "forbidden": sorted(FORBIDDEN_CONTROL_ACTIONS),
                }
            ),
            405,
        )

    @app.post("/api/<path:action>")
    def reject_post_api(action: str) -> tuple[Response, int]:
        lowered = action.lower()
        for bad in FORBIDDEN_CONTROL_ACTIONS:
            if bad.lower() in lowered:
                return (
                    jsonify(
                        {
                            "error": "job injection / control actions are forbidden",
                            "action": action,
                            "read_only": True,
                        }
                    ),
                    403,
                )
        return (
            jsonify({"error": "dashboard API is read-only", "action": action, "read_only": True}),
            405,
        )

    return app
