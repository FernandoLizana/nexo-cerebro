"""Tests auditoría decisiones."""

from __future__ import annotations

from pathlib import Path

import pytest

from nexo.decision_audit import scan_brain_tree
from nexo.decision_port import DecisionPort, DecisionSource
from nexo.paths import repo_root


def test_agency_audit_pass_on_real_brain():
    result = scan_brain_tree()
    assert result["status"] == "audit_pass"
    assert result["files_scanned"] > 50
    assert result["violations"] == []


def test_agency_audit_incomplete_without_brain(tmp_path: Path):
    result = scan_brain_tree(tmp_path / "missing")
    assert result["status"] == "audit_incomplete"
    assert result["ok"] is False


def test_decision_port_rejects_unknown_source():
    with pytest.raises(ValueError):
        DecisionPort.commit(
            choice_key="wander",
            tick=0,
            seed=0,
            config_hash="abc",
            contestants=[],
            limbic_winner_key="",
            pfc_winner_key="",
            inhibited=False,
            margin=0.0,
            legacy_agency_score=0.0,
            selected_by="memory.fake",
        )


def test_decision_port_accepts_prefrontal():
    d = DecisionPort.commit(
        choice_key="wander",
        tick=0,
        seed=0,
        config_hash="abc",
        contestants=[],
        limbic_winner_key="",
        pfc_winner_key="",
        inhibited=False,
        margin=0.0,
        legacy_agency_score=0.0,
        selected_by=DecisionSource.PREFRONTAL_DELIBERATION.value,
    )
    assert d.selected_by == DecisionSource.PREFRONTAL_DELIBERATION.value
