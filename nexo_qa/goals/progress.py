"""Goal progress — derived from observed state, not step lists."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from nexo_qa.goals.models import Goal, GoalProgress, TaskContext


def _url_path(url: str) -> str:
    return urlparse(url).path.lower()


def _query_param(url: str, key: str) -> str:
    return (parse_qs(urlparse(url).query).get(key) or [""])[0]


def evaluate_progress(
    goal: Goal,
    *,
    url: str = "",
    action_history: tuple[str, ...] = (),
    action_labels: dict[str, str] | None = None,
    task_context: TaskContext | None = None,
    policy_blocked: bool = False,
) -> GoalProgress:
    """Ordinal progress from environment evidence — no step counting."""
    ctx = task_context or TaskContext()
    path = _url_path(url)
    labels = " ".join((action_labels or {}).values()).lower()
    history_text = " ".join(action_history).lower()
    evidence: list[str] = []
    satisfied: list[str] = []
    pending: list[str] = list(goal.constraints.keys())

    if policy_blocked:
        return GoalProgress(
            level="blocked",
            status="BLOCKED",
            evidence=("policy_blocked",),
            pending_constraints=tuple(pending),
        )

    desired_plan = (goal.entities.get("plan") or ctx.desired_plan or "").lower()
    level: str = "none"
    status = goal.status if goal.status != "PENDING" else "ACTIVE"

    if "success.html" in path:
        plan = _query_param(url, "plan").lower()
        evidence.append(f"url:success plan={plan or 'unknown'}")
        if desired_plan and plan == desired_plan:
            satisfied.append("must_select_plan")
            level = "complete"
            status = "SATISFIED"
        elif desired_plan:
            level = "partial"
            status = "PARTIALLY_SATISFIED"
            pending = [c for c in pending if c not in satisfied]
        else:
            level = "complete"
            status = "SATISFIED"
    elif "summary.html" in path:
        level = "high"
        status = "PARTIALLY_SATISFIED"
        evidence.append("url:summary")
        if desired_plan and desired_plan in labels + history_text:
            satisfied.append("must_select_plan")
    elif "plan.html" in path:
        level = "partial"
        status = "PARTIALLY_SATISFIED"
        evidence.append("url:plan")
        if desired_plan and desired_plan in labels + history_text:
            satisfied.append("must_select_plan")
            level = "high"
    elif "name.html" in path:
        level = "partial"
        evidence.append("url:name_form")
        if ctx.user_name.lower() in history_text or "type" in history_text:
            satisfied.append("form_started")
    elif "index.html" in path or path.endswith("/"):
        if action_history:
            level = "partial"
            evidence.append("flow_started")
        else:
            level = "none"

    if goal.goal_type == "find_pricing" and "plan.html" in path:
        level = "complete" if level != "none" else "high"
        status = "SATISFIED" if level == "complete" else "PARTIALLY_SATISFIED"
        evidence.append("pricing_section_reached")

    pending = [c for c in pending if c not in satisfied]
    return GoalProgress(
        level=level,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        evidence=tuple(evidence),
        satisfied_constraints=tuple(satisfied),
        pending_constraints=tuple(pending),
    )
