"""Task context builders."""

from __future__ import annotations

from nexo_qa.goals.models import TaskContext


def task_context_from_mapping(data: dict | None) -> TaskContext:
    data = dict(data or {})
    extra = {k: str(v) for k, v in data.items() if k not in ("user_name", "email", "desired_plan", "locale")}
    return TaskContext(
        user_name=str(data.get("user_name", "")),
        email=str(data.get("email", "")),
        desired_plan=str(data.get("desired_plan", "")),
        locale=str(data.get("locale", "es")),
        extra=extra,
    )
