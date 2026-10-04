"""Integrador de conciencia — Global Workspace."""

from brain.consciousness import ConsciousnessIntegrator
from brain.mind import InfantApeBrain


def test_consciousness_selects_winner():
    brain = InfantApeBrain(headless=True)
    brain.world.ensure_home()
    brain.body.hunger = 0.85
    brain.hedonics.tick(brain)
    drives = brain._merged_drives()
    attended = [
        {"label": "hambre", "modality": "interoception", "salience": 0.72, "kind": "body", "valence": -0.2},
    ]
    percepts = attended.copy()
    out = brain.consciousness.integrate(
        brain,
        attended=attended,
        percepts=percepts,
        drives=drives,
        ambient=brain.world.ambient(),
        surprise=0.1,
    )
    assert out.get("winner", {}).get("label")
    assert brain.consciousness.winners
    assert out["metacognition"].get("felt")


def test_consciousness_biases_deliberation():
    from brain.deliberation import ActionContestant

    brain = InfantApeBrain(headless=True)
    brain.body.hunger = 0.9
    brain.hedonics.tick(brain)
    drives = brain._merged_drives()
    attended = [{"label": "hambre", "modality": "interoception", "salience": 0.8, "kind": "body", "valence": -0.3}]
    brain.consciousness.integrate(
        brain,
        attended=attended,
        percepts=attended,
        drives=drives,
        ambient=brain.world.ambient(),
    )
    eat = ActionContestant(key="eat", label="comer", drive="seek_food", go=0.3, net=0.3)
    wander = ActionContestant(key="wander", label="deambular", drive="", go=0.32, net=0.32)
    brain.consciousness.apply_deliberation_bias([eat, wander])
    assert eat.go > wander.go or "eat" in brain.consciousness.action_bias


def test_self_model_narrative():
    ci = ConsciousnessIntegrator()
    assert ci.self_model.identity == "Nexo"


def test_conscious_replay_weight():
    import json
    import time

    from brain.memory_store import EpisodicMemoryStore

    class FakeRow:
        def __init__(self, tags: list[str]) -> None:
            self._data = {
                "valence": 0.2,
                "arousal": 0.4,
                "count": 1,
                "updated_at": time.time(),
                "tags": json.dumps(tags),
            }

        def __getitem__(self, key: str):
            return self._data[key]

    store = EpisodicMemoryStore.__new__(EpisodicMemoryStore)
    now = time.time()
    w_con = store._replay_weight(FakeRow(["conscious", "world"]), now, sleep_phase="nrem_deep")
    w_norm = store._replay_weight(FakeRow(["world"]), now, sleep_phase="nrem_deep")
    assert w_con > w_norm


def test_sync_after_deliberation():
    from brain.deliberation import DeliberationResult

    brain = InfantApeBrain(headless=True)
    brain.deliberation.last = DeliberationResult(
        choice="comer", choice_key="eat", agency=0.72, confidence=0.6
    )
    brain.consciousness.sync_after_deliberation(brain)
    assert brain.consciousness.self_model.last_choice == "comer"
    assert brain.consciousness.self_model.agency == 0.72
