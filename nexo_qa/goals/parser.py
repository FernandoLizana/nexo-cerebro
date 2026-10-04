"""Goal parser — limited NL, no step sequences, no LLM."""

from __future__ import annotations

import re
import uuid

from nexo_qa.goals.models import Goal, TaskContext

SYNONYMS: dict[str, tuple[str, ...]] = {
    "register": ("registro", "registr", "sign up", "signup", "crear cuenta"),
    "plan": ("plan", "subscription", "suscripción", "pricing", "precio", "precios"),
    "pro": ("pro", "premium"),
    "basic": ("basic", "básico", "basico", "free", "gratis"),
    "confirm": ("confirm", "confirmar", "finish", "finalizar", "completar"),
    "navigate": ("encuentra", "find", "buscar", "localizar", "ir a", "go to"),
    "pricing": ("precio", "precios", "pricing", "tarifa", "tarifas"),
}

DOMAIN_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\b(registr|sign\s*up|crear cuenta)\b", "registration"),
    (r"\b(plan|pro|básico|basico|premium|subscription)\b", "plan_selection"),
    (r"\b(precio|precios|pricing|tarifa)\b", "find_pricing"),
    (r"\b(volver|back|anterior|atrás|atras)\b", "navigation"),
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _extract_plan(text: str) -> str:
    lowered = _normalize(text)
    if re.search(r"\bpro\b|premium", lowered):
        return "Pro"
    if re.search(r"\bbásico\b|\bbasico\b|\bbasic\b|\bgratis\b|\bfree\b", lowered):
        return "Basic"
    return ""


def _detect_domain(text: str) -> str:
    lowered = _normalize(text)
    for pattern, domain in DOMAIN_PATTERNS:
        if re.search(pattern, lowered, re.I):
            return domain
    if "complet" in lowered or "finish" in lowered:
        return "registration"
    return "general"


def _derive_subgoals(domain: str, entities: dict[str, str]) -> tuple[str, ...]:
    """Semantic subgoals from goal type — not scenario step lists."""
    if domain == "registration":
        subs = ["localizar_inicio", "completar_informacion", "seleccionar_plan", "confirmar"]
        if entities.get("plan"):
            subs = tuple(s for s in subs if s != "seleccionar_plan") + ("seleccionar_plan",)
        return tuple(subs)
    if domain == "plan_selection":
        return ("localizar_opciones_plan", "seleccionar_plan_objetivo", "confirmar")
    if domain == "find_pricing":
        return ("explorar_sitio", "localizar_seccion_precios",)
    if domain == "navigation":
        return ("retornar_pagina_anterior",)
    return ("explorar_escena", "identificar_accion_relevante")


def parse_goal(description: str, *, task_context: TaskContext | None = None) -> Goal:
    """Raw goal → normalized Goal representation."""
    ctx = task_context or TaskContext()
    normalized = _normalize(description)
    domain = _detect_domain(normalized)
    plan = _extract_plan(normalized) or ctx.desired_plan
    entities: dict[str, str] = {}
    if plan:
        entities["plan"] = plan
    if ctx.user_name:
        entities["name"] = ctx.user_name
    if ctx.email:
        entities["email"] = ctx.email
    constraints: dict[str, str | bool] = {}
    if plan:
        constraints["must_select_plan"] = plan
    if ctx.email:
        constraints["must_use_email"] = ctx.email
    constraints["must_not_leave_allowed_origin"] = True
    subgoals = _derive_subgoals(domain, entities)
    return Goal(
        goal_id=f"goal:{uuid.uuid4().hex[:12]}",
        description=description.strip(),
        goal_type=domain,
        status="PENDING",
        constraints=constraints,
        entities=entities,
        subgoals=subgoals,
        active_subgoal=subgoals[0] if subgoals else None,
        metadata={"normalized": normalized, "parser": "p4_limited_nl"},
    )


def goal_contains_steps(goal_dict: dict) -> bool:
    forbidden = ("expected_actions", "step_sequence", "selectors", "correct_action", "next_step")
    blob = str(goal_dict).lower()
    return any(k in blob for k in forbidden)
