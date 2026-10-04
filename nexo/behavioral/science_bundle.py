"""Bundle ciencia personal — envelope reproducible H1+H2 (Fase 15)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _personal_artifacts(root: Path) -> dict[str, str]:
    base = root / "results" / "personal"
    mapping = {
        "H1_memory_day": base / "H1_memory" / "h1_day_run_seed42.json",
        "H1_interactive": base / "H1_memory" / "h1_interactive_integrated_full_seed42.json",
        "H1_comparison": base / "H1_memory" / "h1_comparison_seed42.json",
        "H1_retention": base / "H1_memory" / "h1_retention_seed42.json",
        "H2_agency": base / "H2_agency" / "h2_agency_audit_seed42.json",
    }
    return {key: str(path) for key, path in mapping.items() if path.exists()}


def export_science_bundle(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    from nexo.behavioral.agency_audit import summarize_agency_audit
    from nexo.behavioral.causal_certificate import summarize_causal_certificates
    from nexo.behavioral.memory_unification import summarize_memory_unification

    personal = _personal_artifacts(repo_root)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "trajectory_hash": result.get("trajectory_hash"),
        "integrated_metrics": {
            "memory_unification": summarize_memory_unification(runtime),
            "causal_certificate": summarize_causal_certificates(runtime),
            "agency_audit": summarize_agency_audit(runtime),
        },
        "personal_artifacts": personal,
        "bitacoras": [
            str(repo_root / "reports" / "personal" / "H1_memory.md"),
            str(repo_root / "reports" / "personal" / "H2_agency.md"),
        ],
        "reproduce": [
            "python -m experiments.personal.run_h1_memory_interactive",
            "python -m experiments.personal.run_h1_memory_retention",
            "python -m experiments.personal.run_h2_agency_audit",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "exported": True,
        "path": str(output_path),
        "personal_artifacts_found": len(personal),
        "science_bundle": True,
    }
