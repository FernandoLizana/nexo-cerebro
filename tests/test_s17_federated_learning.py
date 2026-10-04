"""S17 — Federated learning research tests (opt-in, poison reject, bundle)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.learning.federated.flags import FederatedResearchFlag, ResearchFlagError, require_research_flag
from services.learning.federated.service import FederatedResearchError, FederatedResearchService
from services.learning.federated.updates import ClientUpdate


def _flag() -> FederatedResearchFlag:
    return FederatedResearchFlag(enabled=True, acknowledge_risks=True)


def test_research_flag_off_by_default() -> None:
    with pytest.raises(ResearchFlagError):
        require_research_flag(None)
    with pytest.raises(ResearchFlagError):
        FederatedResearchFlag().validate()
    with pytest.raises(ResearchFlagError):
        FederatedResearchFlag(enabled=True, acknowledge_risks=False).validate()
    with pytest.raises(FederatedResearchError):
        FederatedResearchService(Path("unused"), research_flag=None)


def test_malicious_updates_rejected(tmp_path: Path) -> None:
    svc = FederatedResearchService(tmp_path / "fl", research_flag=_flag(), seed=17)
    svc.register_node("n1")
    svc.register_node("n2")
    rid = svc.begin_round()

    ok = svc.submit_update(
        ClientUpdate(
            node_id="n1",
            round_id=rid,
            weights={"water": 0.2, "berries": 0.3},
            lora_delta={"water": 0.01},
            signature_hex="aa" * 32,
        )
    )
    assert ok["accepted"] is True

    nan = svc.submit_update(
        ClientUpdate(
            node_id="n2",
            round_id=rid,
            weights={"water": float("nan")},
            signature_hex="bb" * 32,
        )
    )
    assert nan["accepted"] is False
    assert "finite" in nan["reason"] or "non-finite" in nan["reason"]

    null_sig = svc.submit_update(
        ClientUpdate(
            node_id="n2",
            round_id=rid,
            weights={"water": 0.1},
            signature_hex="00" * 32,
        )
    )
    assert null_sig["accepted"] is False

    huge = svc.submit_update(
        ClientUpdate(
            node_id="n2",
            round_id=rid,
            weights={"water": 9.0, "x": 9.0, "y": 9.0},
            signature_hex="cc" * 32,
        )
    )
    assert huge["accepted"] is False

    unknown = svc.submit_update(
        ClientUpdate(
            node_id="ghost",
            round_id=rid,
            weights={"water": 0.1},
            signature_hex="dd" * 32,
        )
    )
    assert unknown["accepted"] is False


def test_aggregate_emits_reproducibility_bundle(tmp_path: Path) -> None:
    svc = FederatedResearchService(tmp_path / "fl", research_flag=_flag(), seed=99)
    svc.register_node("n1")
    svc.register_node("n2")
    rid = svc.begin_round()
    svc.submit_update(
        ClientUpdate(
            node_id="n1",
            round_id=rid,
            weights={"berries": 0.4, "water": 0.2},
            signature_hex="11" * 32,
        )
    )
    svc.submit_update(
        ClientUpdate(
            node_id="n2",
            round_id=rid,
            weights={"berries": 0.2, "water": 0.4, "meadow": 0.1},
            lora_delta={"berries": 0.02},
            signature_hex="22" * 32,
        )
    )
    result = svc.aggregate_round(holdout_claims=[{"claim": "berries water meadow"}])
    assert result["auto_deploy_to_core"] is False
    assert result["core_unchanged"] is True
    assert result["accepted"] == 2
    assert result["rejected"] >= 0
    path = Path(result["bundle_path"])
    assert path.is_file()
    bundle = json.loads(path.read_text(encoding="utf-8"))
    assert bundle["format_version"].startswith("nexo-fl-research-bundle")
    assert bundle["auto_deploy_to_core"] is False
    assert bundle["core_unchanged"] is True
    assert bundle["research_flag"]["enabled"] is True
    assert bundle["bundle_hash"]
    assert "disclaimer" in bundle


def test_status_default_enabled_false(tmp_path: Path) -> None:
    svc = FederatedResearchService(tmp_path, research_flag=_flag())
    st = svc.status()
    assert st["default_enabled"] is False
    assert st["auto_deploy_to_core"] is False
    assert st["research_flag"]["enabled"] is True
