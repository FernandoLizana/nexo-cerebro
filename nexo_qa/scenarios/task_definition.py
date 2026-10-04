"""Task definitions — declarative goals for Web Lab scenarios."""

from __future__ import annotations

from nexo_qa.goals.models import TaskContext
from nexo_qa.goals.parser import parse_goal
from nexo_qa.scenarios.browser_lab import GOAL, TEST_DATA

REGISTER_PRO_GOAL = GOAL
REGISTER_PRO_CONTEXT = TaskContext(
    user_name=TEST_DATA["name"],
    email=TEST_DATA["email"],
    desired_plan="Pro",
    locale="es",
)

FIND_PRICING_GOAL = "Encuentra la sección de precios y planes."
FIND_PRICING_CONTEXT = TaskContext(locale="es")

SELECT_PRO_GOAL = "Selecciona el plan Pro."
SELECT_PRO_CONTEXT = TaskContext(desired_plan="Pro", locale="es")


def register_pro_task():
    return parse_goal(REGISTER_PRO_GOAL, task_context=REGISTER_PRO_CONTEXT)


def find_pricing_task():
    return parse_goal(FIND_PRICING_GOAL, task_context=FIND_PRICING_CONTEXT)


def select_pro_task():
    return parse_goal(SELECT_PRO_GOAL, task_context=SELECT_PRO_CONTEXT)
