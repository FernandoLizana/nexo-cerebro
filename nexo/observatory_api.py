"""Observatory read-only API routes — real brain / hub data only."""

from __future__ import annotations

from flask import jsonify


def register_observatory_routes(app, brain):
    """Attach routes that close over the live brain instance."""

    @app.get("/api/dyad/learning")
    def dyad_learning_api():
        """Recent dyad / Nira associations from brain — empty when none yet."""
        nira = list(getattr(brain, "_nira_associations", None) or [])
        dyad = getattr(brain, "_dyad_learning", None)
        nexus_log = list(getattr(brain, "_nexus_dyad_log", None) or [])
        has_data = bool(nira) or bool(dyad) or bool(nexus_log)
        return jsonify(
            {
                "nira_associations": nira[-16:],
                "dyad_learning": dyad if isinstance(dyad, dict) else {},
                "nexus_recent": nexus_log[:12],
                "source": "brain" if has_data else "empty",
                "available": has_data,
                "demo": False,
            }
        )

    @app.get("/api/personalities")
    def personalities_api():
        from brain.personality_archetypes import NEXUS_PROFILE, NIRA_PROFILE, all_presets

        return jsonify(
            {
                "presets": [preset.to_dict() for preset in all_presets()],
                "nexus": dict(NEXUS_PROFILE),
                "nira": dict(NIRA_PROFILE),
                "source": "brain.personality_archetypes",
                "demo": False,
                "note": "Jung-inspired design presets — not clinical typology",
            }
        )

    @app.get("/api/autonomy/decisions")
    def autonomy_decisions_api():
        from brain.character_autonomy import POLICY_VERSION, recent_decisions

        decisions = recent_decisions(limit=16)
        return jsonify(
            {
                "decisions": decisions,
                "policy_version": POLICY_VERSION,
                "source": "brain.character_autonomy",
                "available": bool(decisions),
                "demo": False,
                "note": "character_decision_only_not_disconnect",
            }
        )

    @app.get("/api/relationships")
    def relationships_api():
        """Relationship model snapshot if stored on brain — never invent bonds."""
        raw = getattr(brain, "relationship_model", None)
        if raw is None:
            raw = getattr(brain, "_relationship_model", None)
        if raw is None:
            return jsonify(
                {
                    "relationships": None,
                    "snapshot": None,
                    "source": "empty",
                    "available": False,
                    "demo": False,
                    "friendship_score": None,
                    "note": "no RelationshipModel attached to brain yet",
                }
            )
        if hasattr(raw, "to_dict"):
            snapshot = raw.to_dict()
        elif isinstance(raw, dict):
            snapshot = raw
        else:
            snapshot = None
        return jsonify(
            {
                "relationships": snapshot,
                "snapshot": snapshot,
                "source": "brain",
                "available": snapshot is not None,
                "demo": False,
                "friendship_score": None if snapshot is None else snapshot.get("friendship_score"),
            }
        )

    @app.get("/api/connections/hub")
    def connections_hub_api():
        """Proxy presence hub state — real devices only; unavailable if hub down."""
        from brain.collective_capacity import fetch_hub

        state = fetch_hub()
        if not state:
            return jsonify(
                {
                    "available": False,
                    "source": "unavailable",
                    "hub": None,
                    "demo": False,
                    "note": "presence hub at 127.0.0.1:8770 not reachable — no devices invented",
                }
            )
        return jsonify(
            {
                "available": True,
                "source": "presence_hub",
                "hub": {
                    "name": state.get("name"),
                    "form": state.get("form"),
                    "pose": state.get("pose"),
                    "mood": state.get("mood"),
                    "tick": state.get("tick"),
                    "capacity": state.get("capacity"),
                    "connections": state.get("connections") or [],
                    "links": state.get("links") or {},
                    "traits": state.get("traits") or {},
                },
                "demo": False,
            }
        )


def patch_collective_quarantine(payload: dict, last: dict | None) -> dict:
    """Add quarantine flags to an existing collective payload."""
    last = last or {}
    quarantined = bool(last.get("quarantined")) if last else False
    validated = bool(last.get("validated")) if last else False
    payload["quarantine"] = {
        "quarantined": quarantined,
        "validated": validated,
        "untrusted": quarantined and not validated,
        "last_source": last.get("source") if last else None,
        "last_phrase": last.get("phrase") if last else None,
    }
    if last == {}:
        payload["last"] = None
    return payload
