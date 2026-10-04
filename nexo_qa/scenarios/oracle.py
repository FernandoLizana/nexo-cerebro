"""Scenario oracle — evaluation only, never imported by runtime decision code."""

from __future__ import annotations

from urllib.parse import urlparse

from nexo_qa.scenarios.browser_lab import is_success_url


def success_predicate(url: str, *, required_plan: str | None = None) -> bool:
    return is_success_url(url, required_plan=required_plan)


def failure_predicate(url: str) -> bool:
    return "error" in urlparse(url).path.lower()


def expected_final_state(*, plan: str = "pro") -> dict:
    return {"path_suffix": "success.html", "query_plan": plan.lower()}
