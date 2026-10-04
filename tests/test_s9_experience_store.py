"""S9 — Global Experience Store tests (signature, quarantine, no auto-promote)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from protocols.events.codec import encode_event
from services.experience.models import ExperienceStatus
from services.experience.service import ExperienceError, ExperienceStore
from services.experience.signing import sign_experience
from services.node.identity import load_or_create_identity

ROOT = Path(__file__).resolve().parents[1]
EXP_PKG = ROOT / "services" / "experience"


def _signed_candidate(tmp_path: Path, claim: str = "water is wet"):
    identity, private_key = load_or_create_identity(tmp_path / "node", node_name="n1")
    event = encode_event(
        event_type="KNOWLEDGE_CANDIDATE",
        tick=3,
        payload={"claim": claim, "confidence": 0.7},
    )
    sig = sign_experience(identity, private_key, event=event)
    return identity, private_key, event, sig


def test_ingest_always_quarantines(tmp_path: Path) -> None:
    identity, _, event, sig = _signed_candidate(tmp_path)
    store = ExperienceStore(tmp_path / "exp")
    store.register_node_key(identity.node_id, identity.public_key_pem)
    cand = store.ingest(
        source_node_id=identity.node_id,
        event=event,
        signature_hex=sig.hex(),
    )
    assert cand.status is ExperienceStatus.QUARANTINED
    assert store.stats()["promoted"] == 0
    assert store.stats()["auto_promote"] is False
    assert len(store.list_quarantine()) == 1


def test_bad_signature_rejected_never_promoted(tmp_path: Path) -> None:
    identity, _, event, _ = _signed_candidate(tmp_path)
    store = ExperienceStore(tmp_path / "exp")
    store.register_node_key(identity.node_id, identity.public_key_pem)
    cand = store.ingest(
        source_node_id=identity.node_id,
        event=event,
        signature_hex="00" * 64,
    )
    assert cand.status is ExperienceStatus.QUARANTINED
    validated = store.validate(cand.candidate_id)
    assert validated.status is ExperienceStatus.REJECTED
    assert validated.reject_reason and "signature" in validated.reject_reason.lower()
    with pytest.raises(ExperienceError, match="rejected"):
        store.promote(cand.candidate_id)
    assert store.stats()["promoted"] == 0


def test_quarantine_never_auto_promotes_on_validate(tmp_path: Path) -> None:
    identity, _, event, sig = _signed_candidate(tmp_path)
    store = ExperienceStore(tmp_path / "exp")
    store.register_node_key(identity.node_id, identity.public_key_pem)
    cand = store.ingest(
        source_node_id=identity.node_id,
        event=event,
        signature_hex=sig.hex(),
        auto_validate=True,
    )
    assert cand.status is ExperienceStatus.VALIDATED
    assert cand.status is not ExperienceStatus.PROMOTED
    assert store.stats()["promoted"] == 0
    assert store.list_promoted() == []


def test_explicit_promote_yields_confidence(tmp_path: Path) -> None:
    identity, _, event, sig = _signed_candidate(tmp_path, claim="berries near water")
    store = ExperienceStore(tmp_path / "exp")
    store.register_node_key(identity.node_id, identity.public_key_pem)
    cand = store.ingest(
        source_node_id=identity.node_id,
        event=event,
        signature_hex=sig.hex(),
        auto_validate=True,
    )
    promoted = store.promote(cand.candidate_id)
    assert promoted.status is ExperienceStatus.PROMOTED
    assert promoted.confidence is not None
    assert 0.0 <= promoted.confidence <= 1.0
    assert promoted.promoted_at
    # Survives reload
    store2 = ExperienceStore(tmp_path / "exp")
    again = store2.get(cand.candidate_id)
    assert again.status is ExperienceStatus.PROMOTED
    assert again.confidence == promoted.confidence


def test_cannot_promote_from_quarantine_without_validation(tmp_path: Path) -> None:
    identity, _, event, sig = _signed_candidate(tmp_path)
    store = ExperienceStore(tmp_path / "exp")
    store.register_node_key(identity.node_id, identity.public_key_pem)
    cand = store.ingest(
        source_node_id=identity.node_id,
        event=event,
        signature_hex=sig.hex(),
    )
    with pytest.raises(ExperienceError, match="VALIDATED"):
        store.promote(cand.candidate_id)


def test_experience_package_no_shell_or_sockets() -> None:
    for path in EXP_PKG.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        assert "execute_shell" not in lower or "forbidden" in lower
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in {"socket", "subprocess", "requests"}
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in {"socket", "subprocess", "requests"}
