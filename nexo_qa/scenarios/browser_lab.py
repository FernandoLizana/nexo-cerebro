"""Web Lab scenario — goal and oracle separate from agent knowledge."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

WEB_LAB_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "web_lab"

GOAL = "Completar el flujo de demostración usando el plan Pro."

TEST_DATA = {
    "name": "Nexo Test",
    "email": "nexo@example.test",
}

SUCCESS_PATH_SUFFIX = "/success.html"


def is_success_url(url: str, *, required_plan: str | None = None) -> bool:
    """Test oracle only — not exposed to NEXO."""
    parsed = urlparse(url)
    if not parsed.path.endswith("success.html"):
        return False
    if required_plan:
        from urllib.parse import parse_qs

        qs = parse_qs(parsed.query)
        plan = (qs.get("plan") or [""])[0].lower()
        return plan == required_plan.lower()
    return True


def lab_pages() -> tuple[str, ...]:
    return ("index.html", "name.html", "plan.html", "summary.html", "success.html")
