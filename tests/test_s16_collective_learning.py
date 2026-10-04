"""S16 — Collective Learning tests (eval gates, manual promote, rollback)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from services.learning.models import ArtifactStatus, LearningPhase
from services.learning.service import CollectiveLearningError, CollectiveLearningService

ROOT = Path(__file__).resolve().parents[1]
LEARN_PKG = ROOT / "services" / "learning"

CLAIMS = [
    {"claim": "berries grow near water", "confidence": 0.8},
    {"claim": "water is wet near meadow", "confidence": 0.7},
    {"claim": "foxes explore meadow edges", "confidence": 0.6},
]


def test_ab_distill_and_manual_promote_only(tmp_path: Path) -> None:
    svc = CollectiveLearningService(tmp_path / "learn")
    out = svc.run_ab(claims=CLAIMS, experience_ids=["exp-1"])
    assert out["auto_deploy"] is False
    assert out["manual_promote_only"] is True
    assert out["comparison"]["auto_select_winner"] is False
    a_id = out["phase_a"]["artifact_id"]
    b_id = out["phase_b"]["artifact_id"]
    assert out["phase_a"]["phase"] == "A"
    assert out["phase_b"]["phase"] == "B"

    with pytest.raises(CollectiveLearningError, match="auto promote|forbidden"):
        svc.promote(b_id, allow_auto=True)

    ev = svc.evaluate(b_id)
    assert ev["passed"] is True
    promoted = svc.promote(b_id)
    assert promoted.status is ArtifactStatus.PROMOTED
    assert svc.status()["active"]["artifact_id"] == b_id
    assert svc.status()["auto_deploy"] is False

    # Promote A as second generation
    svc.evaluate(a_id)
    svc.promote(a_id)
    assert svc.status()["active"]["artifact_id"] == a_id

    restored = svc.rollback()
    assert restored.artifact_id == b_id
    assert svc.status()["active"]["artifact_id"] == b_id


def test_eval_gate_rejects_empty(tmp_path: Path) -> None:
    svc = CollectiveLearningService(tmp_path / "learn")
    empty = svc.distill(phase=LearningPhase.A, claims=[{"claim": "", "confidence": 0.9}])
    result = svc.evaluate(empty.artifact_id)
    assert result["passed"] is False
    with pytest.raises(CollectiveLearningError, match="eval gates"):
        svc.promote(empty.artifact_id)


def test_rollback_without_history_fails(tmp_path: Path) -> None:
    svc = CollectiveLearningService(tmp_path / "learn")
    with pytest.raises(CollectiveLearningError, match="no previous"):
        svc.rollback()


def test_package_no_auto_deploy_and_no_fl_default() -> None:
    for path in LEARN_PKG.rglob("*.py"):
        if "federated" in path.parts:
            continue  # S17 opt-in package is separate
        text = path.read_text(encoding="utf-8")
        if "auto_deploy=True" in text or "auto_deploy = True" in text:
            raise AssertionError(f"{path} enables auto_deploy")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in {"socket", "subprocess"}
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in {"socket", "subprocess"}
                assert "federated" not in node.module


def test_disclaimer_present(tmp_path: Path) -> None:
    svc = CollectiveLearningService(tmp_path / "learn")
    out = svc.run_ab(claims=CLAIMS)
    assert "experimental" in out["phase_a"]["disclaimer"].lower()
    assert out["phase_a"]["auto_deploy"] is False
