"""Multi-dimensional relationship state — never collapsed to one friendship score."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

DisagreementKind = Literal["fact", "interpretation", "goal", "preference", "resource"]

_DISAGREE_RE = re.compile(
    r"(?i)\b("
    r"no\s+estoy\s+de\s+acuerdo|no\s+creo|no\s+es\s+cierto|no\s+es\s+verdad|"
    r"incorrecto|mentira|falso|no\s+comparto|"
    r"i\s+disagree|that'?s\s+wrong|not\s+true|i\s+don'?t\s+think"
    r")\b"
)
_PREFERENCE_RE = re.compile(r"(?i)\b(prefiero|me\s+gusta|no\s+me\s+gusta|rather|prefer)\b")
_GOAL_RE = re.compile(r"(?i)\b(quiero|objetivo|meta|goal|vamos\s+a|let'?s)\b")
_FACT_RE = re.compile(
    r"(?i)\b(es\s+un\s+hecho|de\s+hecho|fact|verdad|cierto|incorrecto|falso|no\s+es\s+cierto)\b"
)


def classify_dyad_disagreement(nexo_line: str, nira_line: str) -> DisagreementKind | None:
    """Heuristic: Nira pushback against Nexo → typed disagreement, else None."""
    reply = (nira_line or "").strip()
    if not reply:
        return None
    if not (_DISAGREE_RE.search(reply) or reply.lower().startswith("no,") or reply.lower().startswith("no ")):
        return None
    blob = f"{nexo_line} {nira_line}"
    if _FACT_RE.search(blob):
        return "fact"
    if _PREFERENCE_RE.search(blob):
        return "preference"
    if _GOAL_RE.search(blob):
        return "goal"
    return "interpretation"


def note_dyad_exchange(
    model: RelationshipModel,
    *,
    nexo_line: str,
    nira_line: str,
    trigger: str = "dyad",
) -> dict[str, Any]:
    """Record cooperation and optional disagreement after a Nexus↔Nira turn.

    Affinity / trust updates never verify learning claims — use dyad_learning.promote_if_verified.
    """
    model.record_cooperation(
        domain="dialogue",
        success=True,
        note=f"dyad:{trigger}"[:200],
    )
    kind = classify_dyad_disagreement(nexo_line, nira_line)
    disagreement: dict[str, Any] | None = None
    if kind is not None:
        topic = (nira_line or nexo_line or trigger)[:120]
        disagreement = model.record_disagreement(
            kind,
            topic=topic,
            domain="dialogue",
            severity=0.35,
        )
    return {
        "cooperation": True,
        "disagreement": disagreement,
        "kind": kind,
        "friendship_score": None,
    }


@dataclass
class RelationshipModel:
    """Independent axes for dyad / peer bonds."""

    affinity: float = 0.35
    trust_by_domain: dict[str, float] = field(default_factory=dict)
    cooperation_history: list[dict[str, Any]] = field(default_factory=list)
    pending_disagreements: list[dict[str, Any]] = field(default_factory=list)
    repair_experiences: list[dict[str, Any]] = field(default_factory=list)
    reciprocity: float = 0.5
    exchange_limits: dict[str, float] = field(
        default_factory=lambda: {"attention": 1.0, "compute": 1.0, "disclosure": 0.6}
    )

    def trust(self, domain: str, default: float = 0.5) -> float:
        return float(self.trust_by_domain.get(domain, default))

    def record_cooperation(
        self,
        *,
        domain: str,
        success: bool,
        note: str = "",
        delta_reciprocity: float = 0.02,
    ) -> None:
        self.cooperation_history.append(
            {
                "domain": domain,
                "success": bool(success),
                "note": str(note)[:200],
            }
        )
        self.cooperation_history = self.cooperation_history[-48:]
        if success:
            self.affinity = min(1.0, self.affinity + 0.02)
            self.reciprocity = min(1.0, self.reciprocity + abs(delta_reciprocity))
            prev = self.trust(domain)
            self.trust_by_domain[domain] = min(1.0, prev + 0.04)
        else:
            self.affinity = max(0.0, self.affinity - 0.01)
            prev = self.trust(domain)
            self.trust_by_domain[domain] = max(0.0, prev - 0.03)

    def record_disagreement(
        self,
        kind: DisagreementKind,
        *,
        topic: str,
        domain: str = "general",
        severity: float = 0.3,
    ) -> dict[str, Any]:
        entry = {
            "kind": kind,
            "topic": str(topic)[:200],
            "domain": domain,
            "severity": float(max(0.0, min(1.0, severity))),
            "status": "pending",
        }
        self.pending_disagreements.append(entry)
        self.pending_disagreements = self.pending_disagreements[-24:]
        # Affinity and domain trust move independently of reciprocity / limits.
        if kind == "fact":
            self.trust_by_domain[domain] = max(0.0, self.trust(domain) - 0.05 * severity)
        elif kind == "preference":
            self.affinity = max(0.0, self.affinity - 0.02 * severity)
        elif kind == "resource":
            lim = float(self.exchange_limits.get(domain, 1.0))
            self.exchange_limits[domain] = max(0.1, lim - 0.1 * severity)
        return entry

    def propose_check(self, *, domain: str, cost: float = 0.2) -> dict[str, Any]:
        """Whether an exchange is within limits given current trust/reciprocity."""
        limit = float(self.exchange_limits.get(domain, self.exchange_limits.get("attention", 1.0)))
        trust = self.trust(domain)
        ok = cost <= limit and trust >= 0.25 and self.reciprocity >= 0.2
        return {
            "ok": ok,
            "domain": domain,
            "cost": cost,
            "limit": limit,
            "trust": trust,
            "reciprocity": self.reciprocity,
            "affinity": self.affinity,
        }

    def apply_repair(
        self,
        *,
        topic: str | None = None,
        domain: str = "general",
        note: str = "",
    ) -> dict[str, Any]:
        repaired: list[dict[str, Any]] = []
        remaining: list[dict[str, Any]] = []
        for d in self.pending_disagreements:
            match_topic = topic is None or d.get("topic") == topic
            match_domain = d.get("domain") == domain
            if match_topic and match_domain and d.get("status") == "pending":
                fixed = {**d, "status": "repaired", "note": note[:120]}
                repaired.append(fixed)
                self.repair_experiences.append(fixed)
            else:
                remaining.append(d)
        self.pending_disagreements = remaining
        self.repair_experiences = self.repair_experiences[-32:]
        if repaired:
            self.affinity = min(1.0, self.affinity + 0.03 * len(repaired))
            self.trust_by_domain[domain] = min(1.0, self.trust(domain) + 0.05)
            self.reciprocity = min(1.0, self.reciprocity + 0.02)
        return {"repaired": repaired, "pending": len(self.pending_disagreements)}

    def to_dict(self) -> dict[str, Any]:
        return {
            "affinity": round(self.affinity, 4),
            "trust_by_domain": {k: round(float(v), 4) for k, v in self.trust_by_domain.items()},
            "cooperation_history": list(self.cooperation_history)[-16:],
            "pending_disagreements": list(self.pending_disagreements),
            "repair_experiences": list(self.repair_experiences)[-16:],
            "reciprocity": round(self.reciprocity, 4),
            "exchange_limits": {k: round(float(v), 4) for k, v in self.exchange_limits.items()},
            # Explicit: no single friendship score.
            "friendship_score": None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RelationshipModel:
        data = data or {}
        return cls(
            affinity=float(data.get("affinity", 0.35)),
            trust_by_domain={str(k): float(v) for k, v in (data.get("trust_by_domain") or {}).items()},
            cooperation_history=list(data.get("cooperation_history") or []),
            pending_disagreements=list(data.get("pending_disagreements") or []),
            repair_experiences=list(data.get("repair_experiences") or []),
            reciprocity=float(data.get("reciprocity", 0.5)),
            exchange_limits={
                str(k): float(v)
                for k, v in (
                    data.get("exchange_limits")
                    or {"attention": 1.0, "compute": 1.0, "disclosure": 0.6}
                ).items()
            },
        )
