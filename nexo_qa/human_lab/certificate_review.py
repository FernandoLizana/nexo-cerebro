"""Cognitive Failure Certificate review pipeline."""

from __future__ import annotations

from typing import Any

FORBIDDEN_CAUSAL = ("caused_by", "proven_cause")
ALLOWED_CAUSAL = ("associated_with", "preceded", "contributed_to")


def review_certificate(cert: dict[str, Any]) -> dict[str, Any]:
    failure = cert.get("failure") or {}
    wording = str(failure.get("causal_relation", failure.get("relationship", "")))
    issues: list[str] = []
    if any(w in wording for w in FORBIDDEN_CAUSAL):
        issues.append("causal wording too strong")
    evidence = cert.get("evidence") or []
    if not evidence:
        issues.append("missing evidence")
    for token in ("data-testid", "xpath", "css", "selector"):
        blob = str(cert).lower()
        if token in blob:
            issues.append(f"selector leakage: {token}")
    return {
        "certificate_id": cert.get("certificate_id"),
        "evidence_ok": bool(evidence),
        "classification_plausible": failure.get("failure_type") is not None,
        "causal_wording_ok": not issues or "causal wording" not in " ".join(issues),
        "issues": issues,
        "allowed_relations": list(ALLOWED_CAUSAL),
    }
