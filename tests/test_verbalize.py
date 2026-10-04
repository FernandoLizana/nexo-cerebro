from brain.verbalize import format_episode_label, humanize_memory_label


def test_humanize_technical_label():
    assert humanize_memory_label("dormir@casa@422") == "cuando quise dormir en casa"
    assert humanize_memory_label("comer@casa@317") == "cuando comí en casa"


def test_format_episode_label():
    assert format_episode_label("dormir", "casa") == "dormir en casa"
    assert format_episode_label("deambular", "escritorio") == "deambular en el escritorio"


def test_imagination_compound():
    out = humanize_memory_label("imaginación: comer@casa@317 · dormir@casa@308")
    assert "comí" in out and "dormir" in out
