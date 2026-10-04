"""RelationshipModel: independent axes, repair, affinity ≠ verification."""

from __future__ import annotations

from brain.dyad_learning import LearningRecord, nira_receptive_step, promote_if_verified
from brain.relationship_model import RelationshipModel, note_dyad_exchange


def test_dimensions_move_independently() -> None:
    rm = RelationshipModel(affinity=0.5, reciprocity=0.5)
    rm.trust_by_domain["science"] = 0.6
    before_aff = rm.affinity
    before_rec = rm.reciprocity
    before_sci = rm.trust("science")

    rm.record_disagreement("fact", topic="gravity", domain="science", severity=1.0)
    assert rm.trust("science") < before_sci
    assert rm.affinity == before_aff  # fact → domain trust, not affinity
    assert rm.reciprocity == before_rec

    before_aff = rm.affinity
    before_sci = rm.trust("science")
    rm.record_disagreement("preference", topic="color", domain="science", severity=1.0)
    assert rm.affinity < before_aff
    assert rm.trust("science") == before_sci  # preference does not burn science trust

    snap = rm.to_dict()
    assert snap["friendship_score"] is None
    assert "affinity" in snap and "reciprocity" in snap


def test_repair_clears_pending_and_restores() -> None:
    rm = RelationshipModel(affinity=0.4)
    rm.record_disagreement("interpretation", topic="weather", domain="dialogue")
    assert len(rm.pending_disagreements) == 1
    out = rm.apply_repair(topic="weather", domain="dialogue", note="clarified")
    assert out["repaired"]
    assert out["pending"] == 0
    assert rm.pending_disagreements == []
    assert rm.repair_experiences
    assert rm.affinity > 0.4


def test_positive_affinity_does_not_verify_false_claims() -> None:
    """High bond must not promote associations; only promote_if_verified + evidence."""
    rm = RelationshipModel(affinity=0.99)
    for _ in range(5):
        rm.record_cooperation(domain="dialogue", success=True, note="chat")
    assert rm.affinity >= 0.99 or rm.affinity > 0.9

    claim = nira_receptive_step(
        experience="la luna es queso",
        prior_memory="cuentos",
        authorized=True,
    )
    assert claim.kind == "symbolic_association"
    assert claim.validated is False

    # Affinity alone must not verify.
    still = promote_if_verified(claim, evidence_ok=False)
    assert still.kind == "symbolic_association"
    assert still.validated is False

    verified = promote_if_verified(claim, evidence_ok=True)
    assert verified.kind == "verified"
    assert verified.validated is True

    # Explicit false claim record stays non-verified without evidence.
    false_claim = LearningRecord(
        actor="nira",
        kind="hypothesis",
        content="2+2=5",
        provenance="social_guess",
        validated=False,
    )
    assert promote_if_verified(false_claim, evidence_ok=False).kind == "hypothesis"


def test_note_dyad_exchange_records_cooperation_and_disagreement() -> None:
    rm = RelationshipModel()
    note_dyad_exchange(
        rm,
        nexo_line="El cielo es verde.",
        nira_line="No es cierto, el cielo es azul.",
        trigger="test",
    )
    assert rm.cooperation_history
    assert rm.cooperation_history[-1]["success"] is True
    assert any(d.get("kind") == "fact" for d in rm.pending_disagreements)
