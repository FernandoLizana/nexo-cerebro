"""Cognitive Failure Certificate — auditable QA artifact."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

from nexo_qa.analysis.models import RawRunTrace
from nexo_qa.failures.taxonomy import CLASSIFICATION_VERSION, CognitiveFailure

CERTIFICATE_SCHEMA_VERSION = 1
METRICS_VERSION = "metrics-v1"

FORBIDDEN_PATTERNS = re.compile(
    r"data-testid|xpath|css selector|playwright|#[0-9a-f]{3,8}\b|password|token|secret",
    re.IGNORECASE,
)


@dataclass
class CognitiveFailureCertificate:
    certificate_id: str
    schema_version: int = CERTIFICATE_SCHEMA_VERSION
    classification_version: str = CLASSIFICATION_VERSION
    metrics_version: str = METRICS_VERSION
    run: dict[str, Any] = field(default_factory=dict)
    goal: dict[str, Any] = field(default_factory=dict)
    persona: dict[str, Any] = field(default_factory=dict)
    perception: dict[str, Any] = field(default_factory=dict)
    cognition: dict[str, Any] = field(default_factory=dict)
    decision: dict[str, Any] = field(default_factory=dict)
    expectation: dict[str, Any] = field(default_factory=dict)
    outcome: dict[str, Any] = field(default_factory=dict)
    failure: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)

    def content_hash(self) -> str:
        blob = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "certificate_id": self.certificate_id,
            "schema_version": self.schema_version,
            "classification_version": self.classification_version,
            "metrics_version": self.metrics_version,
            "run": dict(self.run),
            "goal": dict(self.goal),
            "persona": dict(self.persona),
            "perception": dict(self.perception),
            "outcome": dict(self.outcome),
            "cognition": dict(self.cognition),
            "decision": dict(self.decision),
            "expectation": dict(self.expectation),
            "failure": dict(self.failure),
            "evidence": list(self.evidence),
            "calibration_disclaimer": "simulation-derived; not human-calibrated",
        }
        payload["content_hash"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        return payload


def build_certificate(
    raw: RawRunTrace,
    failure: CognitiveFailure,
    *,
    certificate_id: str | None = None,
) -> CognitiveFailureCertificate:
    """Build certificate for one failure episode."""
    from uuid import uuid4

    meta = raw.metadata
    cid = certificate_id or f"CQF-{uuid4().hex[:6].upper()}"
    progress = meta.get("final_progress") or {}
    action_history = list(meta.get("action_history") or [])
    selected = action_history[-1] if action_history else None
    goal_rel = dict(meta.get("goal_relevance") or {})
    alternatives = [
        {"action_id": aid, "label": aid, "goal_relevance": round(float(goal_rel.get(aid, 0.0)), 4)}
        for aid in sorted(goal_rel.keys())[:8]
    ]

    visible: list[str] = []
    attended: list[str] = []
    scene_id = None
    for wt in raw.world_trace:
        if wt.get("event_type") == "PERCEPTUAL_SCENE":
            payload = wt.get("payload") or {}
            scene_id = payload.get("scene_id")
            for p in payload.get("percepts") or []:
                label = p.get("label") or p.get("text") or ""
                if label:
                    visible.append(str(label)[:80])
        if wt.get("event_type") == "ATTENTION_TRACE":
            payload = wt.get("payload") or {}
            attended = [str(x) for x in (payload.get("attended") or [])[:12]]

    pstate = meta.get("persona_state") or {}
    cert = CognitiveFailureCertificate(
        certificate_id=cid,
        run={"run_id": raw.run_id, "seed": raw.seed, "ticks": raw.ticks},
        goal={
            "id": meta.get("goal_id"),
            "description": meta.get("goal_description", ""),
            "progress_before": progress.get("level", "unknown"),
            "progress_after": progress.get("level", "unknown"),
        },
        persona={
            "persona_id": meta.get("persona_id"),
            "traits_summary": meta.get("persona_traits"),
        },
        perception={
            "scene_id": scene_id,
            "visible": visible[:12],
            "attended": attended[:12],
        },
        cognition={
            "frustration": pstate.get("current_frustration"),
            "fatigue": pstate.get("current_fatigue"),
            "confidence": pstate.get("current_confidence"),
        },
        decision={
            "alternatives": alternatives,
            "selected": {"action_id": selected} if selected else {},
        },
        expectation={"expected_effect": "goal_progress_improvement"},
        outcome={
            "actual_effect": progress.get("status", "unknown"),
            "progress_delta": progress.get("level", "unknown"),
        },
        failure=failure.to_dict(),
        evidence=[{"event_ref": eid, "type": "primary"} for eid in failure.primary_evidence],
    )
    return cert


def validate_certificate(cert: CognitiveFailureCertificate) -> list[str]:
    """Validate schema, evidence, selector secrecy."""
    errors: list[str] = []
    if cert.schema_version < 1:
        errors.append("invalid schema_version")
    if not cert.classification_version:
        errors.append("missing classification_version")
    if not cert.failure:
        errors.append("missing failure block")
    blob = json.dumps(cert.to_dict()).lower()
    if FORBIDDEN_PATTERNS.search(blob):
        errors.append("forbidden selector/secret pattern detected")
    for key in ("css", "xpath", "data-testid", "selector"):
        if key in blob:
            errors.append(f"selector leakage: {key}")
    if not cert.evidence and cert.failure:
        errors.append("failure without evidence refs")
    return errors
