"""Symbol cards: shape of the deck, and graceful load of an old saved world.

The legacy key names live in brain.archetype_cards. This file only refers to
those constants, then writes them into a fabricated temporary directory.
"""

from __future__ import annotations

import json

from brain.archetype_cards import (
    LEGACY_ID_PREFIX,
    LEGACY_KIND,
    LEGACY_META_KEY,
    LEGACY_STATS_KEY,
    LEGACY_TOUCH_EVENT,
    TOUCH_EVENT,
    all_cards,
    card_from_object,
    get_card,
    is_touch_event,
    legacy_stats,
    normalize_card_meta,
)
from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE


def test_deck_has_twenty_two_jungian_symbols() -> None:
    cards = all_cards()
    assert len(cards) == 22
    assert len({card.key for card in cards}) == 22
    assert get_card("self").name_es.startswith("El Sí-mismo")
    assert get_card("anima").key == "anima"
    rebirth = get_card("death")
    assert rebirth is not None and rebirth.key == "rebirth"
    assert card_from_object(f"{LEGACY_ID_PREFIX}tower", "").key == "inflation"


def test_legacy_meta_normalizes_without_dropping_the_card() -> None:
    meta = normalize_card_meta({LEGACY_META_KEY: "death", "kind": LEGACY_KIND, "touched": True})
    assert meta["archetype_card"] == "rebirth"
    assert meta["kind"] == "archetype_card"
    assert meta["touched"] is True
    assert LEGACY_META_KEY not in meta
    assert is_touch_event(LEGACY_TOUCH_EVENT)
    assert is_touch_event(TOUCH_EVENT)
    assert legacy_stats({LEGACY_STATS_KEY: {"total": 0, "untouched": 0}})["total"] == 0
    assert legacy_stats({LEGACY_STATS_KEY: "not-a-block"}) is None
    assert legacy_stats(None) is None


def test_old_saved_world_loads_from_a_fabricated_directory(tmp_path) -> None:
    """A copy built in tmp, never the user's data/brain_state."""
    state = tmp_path / "fabricated_state"
    writer = InfantApeBrain(profile=COMPACT_PROFILE, state_dir=state, auto_save=False)
    writer.save_state()
    meta_path = state / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    world = meta["world"]
    world[LEGACY_STATS_KEY] = {
        "total": 1,
        "untouched": 1,
        "uninternalized": 1,
        "internalized": 0,
    }
    world["objects"] = [
        {
            "id": f"{LEGACY_ID_PREFIX}death",
            "kind": "book",
            "x": 40.0,
            "y": 40.0,
            "label": "La Muerte",
            "modality": "text",
            "zone": "desk",
            "meta": {LEGACY_META_KEY: "death", "kind": LEGACY_KIND},
        }
    ]
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    reader = InfantApeBrain(profile=COMPACT_PROFILE, state_dir=state, auto_save=False)
    loaded = reader.load_state()
    assert loaded.get("loaded") is True
    cards = [obj for obj in reader.world.objects if obj.meta.get("archetype_card")]
    assert len(cards) == 1
    assert cards[0].meta["archetype_card"] == "rebirth"
    assert LEGACY_META_KEY not in cards[0].meta
    snap = reader.world.to_dict()
    assert LEGACY_STATS_KEY not in snap
    assert snap["archetype_cards"]["total"] == 1
    assert snap["objects"][0]["meta"]["archetype_card"] == "rebirth"
