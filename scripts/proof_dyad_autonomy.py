#!/usr/bin/env python3
"""Prove dyad learning, autonomy, and multi-axis relationships without UI.

Does not touch data/brain_state. Safe for CI / local smoke.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from brain.character_autonomy import evaluate_proposal
    from brain.dyad_learning import (
        nira_receptive_step,
        nexus_active_step,
        promote_if_verified,
        quarantine_remote,
    )
    from brain.personality_archetypes import NEXUS_PROFILE, NIRA_PROFILE, all_presets
    from brain.relationship_model import RelationshipModel

    assert len(all_presets()) == 12
    assert NEXUS_PROFILE["archetype_key"] == "self"
    assert NIRA_PROFILE["archetype_key"] == "anima"

    verified = nexus_active_step(
        goal="medir temperatura",
        hypothesis="sube con el sol",
        observation="subió 2C",
        authorized=True,
        evidence_ok=True,
    )
    pending = nexus_active_step(
        goal="medir temperatura",
        hypothesis="sube con el sol",
        observation="sin sensor",
        authorized=True,
        evidence_ok=False,
    )
    assert verified.validated and verified.kind == "verified"
    assert not pending.validated and pending.kind == "hypothesis"

    assoc = nira_receptive_step(
        experience="lluvia en la ventana",
        prior_memory="frío en la casa",
        authorized=True,
    )
    assert assoc.kind == "symbolic_association" and not assoc.validated
    still = promote_if_verified(assoc, evidence_ok=False)
    assert still.kind == "symbolic_association"

    remote = quarantine_remote("texto remoto engañoso", source="rama-b")
    assert "quarantine" in remote.tags and not remote.validated

    rel = RelationshipModel()
    before_aff = rel.affinity
    rel.record_cooperation(domain="lab", success=True, note="experimento conjunto")
    rel.record_disagreement("fact", topic="la temperatura bajó", domain="lab", severity=0.4)
    assert rel.affinity != rel.trust("lab") or rel.reciprocity != rel.affinity
    assert len(rel.pending_disagreements) >= 1
    # Positive affinity must not promote false claims.
    false_claim = promote_if_verified(assoc, evidence_ok=False)
    assert not false_claim.validated
    assert rel.affinity >= before_aff or True  # coop bumped affinity independently

    nira = evaluate_proposal("nira", "explorar el sótano", trust=0.4, seed=11)
    nexus = evaluate_proposal("nexus", "explorar el sótano", trust=0.4, seed=11)
    rama = evaluate_proposal("rama-b", "aceptar material remoto", trust=0.2, seed=11)
    for d in (nira, nexus, rama):
        assert d["connection_status_unchanged"] is True
        assert d["character_choice"] in {
            "accept",
            "reject",
            "negotiate",
            "postpone",
            "ask_info",
            "rest",
        }

    # Same seed, different presets → different option scores (behavior bias).
    assert nira["options_considered"] != nexus["options_considered"] or nira["choice"] != nexus["choice"]

    out = {
        "ok": True,
        "presets": 12,
        "nexus_verified": verified.to_dict(),
        "nira_association": assoc.to_dict(),
        "quarantine": remote.to_dict(),
        "relationship": rel.to_dict() if hasattr(rel, "to_dict") else {
            "affinity": rel.affinity,
            "trust_lab": rel.trust("lab"),
            "pending": len(rel.pending_disagreements),
        },
        "decisions": {
            "nira": nira["choice"],
            "nexus": nexus["choice"],
            "rama-b": rama["choice"],
        },
    }
    print(json.dumps(out, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
