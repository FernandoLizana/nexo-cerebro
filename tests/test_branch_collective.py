"""Branches meet at random, both learn, and that raises central capacity."""

from types import SimpleNamespace

from brain.collective_capacity import apply_capacity, probe_retention
from brain.working_memory import WorkingMemory


class _Hippo:
    def __init__(self) -> None:
        self.capacity = 96


def test_two_branches_exchange_and_raise_capacity(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("NEXO_PRESENCE_STATE", str(tmp_path / "hub.json"))
    import importlib
    import services.presence.hub as hub

    importlib.reload(hub)
    hub.interact("rama", "TEACH", "el mango contiene vitamina c")
    hub.interact("rama-b", "TEACH", "la ceiba da sombra ancha")
    hub.interact("android-cerebro", "GREET")
    hub.interact("android-nodo", "GREET")
    paired = hub.pair_random()
    assert paired["ok"] is True
    books = paired["state"]["notebooks"]
    a, b = paired["a"], paired["b"]
    assert books[a][-1]["from"] == b
    assert books[b][-1]["from"] == a
    assert books[a][-1]["text"]
    assert paired["capacity"] > 8
    ask_a = hub.interact(a, "ASK", books[a][-1]["text"].split()[0])
    assert ask_a["ok"] and "aprendí" in ask_a["result"]["speech"]


def test_connection_grows_real_working_memory() -> None:
    brain = SimpleNamespace(working_memory=WorkingMemory(capacity=7), hippocampus=_Hippo())
    before = brain.working_memory.effective_capacity()
    grown = apply_capacity(
        brain,
        {"connections": [{"strength": 2}, {"strength": 1}], "capacity": 16},
    )
    assert grown["wm_after"] == before + 2
    assert grown["not_connectome"] is True
    assert grown["retention_ok"] is True
    assert grown["retained_wm_slots"] == before + 2
    assert brain.hippocampus.capacity == 96 + 16
    probe = probe_retention(brain)
    assert probe["ok"] and probe["held"] == before + 2


def test_hub_state_survives_reload(tmp_path, monkeypatch) -> None:
    path = tmp_path / "hub.json"
    monkeypatch.setenv("NEXO_PRESENCE_STATE", str(path))
    import importlib
    import services.presence.hub as hub

    importlib.reload(hub)
    hub.interact("rama", "TEACH", "persistencia de la ceiba")
    hub.interact("rama-b", "TEACH", "persistencia del mango")
    hub.pair_random()
    capacity = hub.snapshot()["capacity"]
    importlib.reload(hub)
    restored = hub.snapshot()
    assert restored["capacity"] == capacity
    assert any(restored["notebooks"][sid] for sid in ("rama", "rama-b"))


def test_lonely_branch_does_not_pair(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("NEXO_PRESENCE_STATE", str(tmp_path / "lonely.json"))
    import importlib
    import services.presence.hub as hub

    importlib.reload(hub)
    saved = {sid: dict(link) for sid, link in hub._STATE["links"].items()}
    hub._STATE["links"] = {sid: {"online": sid == "rama", "last": None} for sid in saved}
    try:
        assert hub.pair_random()["ok"] is False
    finally:
        hub._STATE["links"] = saved
