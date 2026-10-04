"""Stream de imaginación continuo."""

from brain.mind import InfantApeBrain


def test_imagination_stream_always_active():
    brain = InfantApeBrain()
    thought = brain.think(vision=brain._scan_vision())
    im = brain.imagination.advance_stream(brain, thought=thought, vision=brain._last_vision)
    assert im["active"] is True
    assert im["streaming"] is True
    assert im.get("image_b64")
    assert im.get("sources")

    im2 = brain.imagination.advance_stream(brain, thought=thought, vision=brain._last_vision)
    assert im2["frame"] > im["frame"]


def test_user_interact_rejects_motor_orders():
    brain = InfantApeBrain()
    try:
        brain.user_interact(action="walk", x=100, y=100)
        assert False, "should raise"
    except ValueError as e:
        assert "autónomo" in str(e).lower() or "órdenes" in str(e).lower()
