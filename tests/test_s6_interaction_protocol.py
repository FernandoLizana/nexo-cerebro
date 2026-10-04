"""S6 — BIP / Event protocol tests."""

from __future__ import annotations

import pytest

from protocols.being_interaction.codec import BIPError, decode_interaction, encode_interaction
from protocols.being_interaction.privacy import PrivacyViolation, sanitize_interaction_context
from protocols.events.codec import EventProtocolError, decode_event, encode_event
from services.being.creator import create_being
from services.being.models import BeingArchetype, BeingSpecies
from services.worlds.textworld.runner import run_textworld_experiment


def test_bip_round_trip_and_reject_unknown() -> None:
    raw = encode_interaction(
        kind="PLAY",
        being_a="being-a",
        being_b="being-b",
        tick=3,
        place="meadow",
        response="play_accepted",
        outcome="play",
        context={"raw_action": "play_being-b"},
    )
    again = decode_interaction(raw)
    assert again.kind.value == "PLAY"
    assert again.to_dict()["version"] == "bip-v1"
    with pytest.raises(BIPError, match="not allowlisted"):
        encode_interaction(kind="EXECUTE_SHELL", being_a="a", being_b=None, tick=0)
    with pytest.raises(BIPError, match="not allowlisted"):
        decode_interaction({"version": "bip-v1", "kind": "LOVE_REAL", "being_a": "a", "tick": 0})


def test_privacy_filter_blocks_user_chat() -> None:
    with pytest.raises(PrivacyViolation):
        sanitize_interaction_context({"user_chat": "hello from human"})
    with pytest.raises(PrivacyViolation):
        encode_interaction(
            kind="MESSAGE",
            being_a="a",
            being_b="b",
            tick=1,
            context={"private_chat": "secret talk"},
        )
    clean = sanitize_interaction_context({"raw_action": "observe", "note": "world-only"})
    assert clean["raw_action"] == "observe"


def test_event_protocol_round_trip() -> None:
    ev = encode_event(
        event_type="BEING_INTERACTION",
        tick=2,
        payload={
            "kind": "GREET",
            "being_a": "a",
            "being_b": "b",
            "place": "den",
            "outcome": "social_contact",
            "context": {"raw_action": "greet_b"},
        },
    )
    decoded = decode_event(ev)
    assert decoded.event_type.value == "BEING_INTERACTION"
    assert decoded.payload["kind"] == "GREET"
    with pytest.raises(EventProtocolError, match="not allowlisted"):
        encode_event(event_type="HACK_NETWORK", tick=0, payload={})


def test_textworld_emits_valid_bip_events() -> None:
    a = create_being(
        name="A",
        species=BeingSpecies.HUMANOID,
        archetype=BeingArchetype.EXPLORER,
        creator_node="n",
        traits={"sociability": 0.95},
    )
    b = create_being(
        name="B",
        species=BeingSpecies.ANIMAL,
        archetype=BeingArchetype.DOG,
        creator_node="n",
        traits={"sociability": 0.9},
    )
    result = run_textworld_experiment(
        [a, b],
        seed=11,
        ticks=20,
        initial_places={a.identity.being_id: "meadow", b.identity.being_id: "meadow"},
    )
    interactions = [e for e in result["events"] if e["event_type"] == "BEING_INTERACTION"]
    assert interactions
    for ev in interactions:
        decoded = decode_event(ev)
        assert decoded.payload["version"] == "bip-v1"
        assert "user_chat" not in decoded.payload.get("context", {})
