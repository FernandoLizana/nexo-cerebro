"""The four presence sources and four interactions must succeed."""

from __future__ import annotations

import json
import urllib.request

from services.presence.hub import interact


def test_four_kinds_always_work() -> None:
    greet = interact("local", "GREET")
    observe = interact("rama", "OBSERVE", "la luz cambia")
    teach = interact("android-cerebro", "TEACH", "el fuego calienta")
    ask = interact("android-nodo", "ASK", "fuego")
    assert greet["ok"] and observe["ok"] and teach["ok"] and ask["ok"]
    assert "calienta" in ask["result"]["speech"]
    assert ask["state"]["links"]["android-nodo"]["online"] is True
    assert ask["state"]["capacity"] > 8
    assert ask["state"]["connections"]
    assert "se cruza" in ask["state"]["ideas"][-1]["text"]


def test_node_material_waits_until_central_takes(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("NEXO_NODE_SHELF", str(tmp_path))
    from brain.node_offerings import peek_offering, take_offering
    from services.presence.shelf import accept

    held = accept("android-nodo", "nota.txt", "el agua corre".encode())
    assert held["ok"] is True
    assert peek_offering()["status"] == "held"
    taken = take_offering()
    assert taken and "agua" in taken["text"]
    assert peek_offering() is None
    assert accept("local", "nota.txt", b"no")["ok"] is False
    assert accept("rama", "run.exe", b"no")["ok"] is False
    image = accept("rama", "gato.png", b"\x89PNG\r\n", note="un gato en la alfombra")
    assert image["ok"] and image["item"]["kind"] == "image"


def test_unknown_kind_fails_closed() -> None:
    assert interact("local", "EXECUTE_SHELL")["ok"] is False


def test_http_roundtrip(monkeypatch) -> None:
    monkeypatch.setenv("NEXO_PRESENCE_TOKEN", "test-presence-token-32c!!")
    from services.presence.hub import reset_presence_auth, serve

    reset_presence_auth()
    httpd = serve(port=0)
    port = httpd.server_address[1]
    try:
        body = json.dumps({"source": "local", "kind": "TEACH", "text": "el agua corre"}).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/interact",
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Nexo-Presence-Token": "test-presence-token-32c!!",
            },
        )
        with urllib.request.urlopen(req, timeout=3) as res:
            payload = json.loads(res.read().decode())
        assert payload["ok"] is True
        page = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=3).read().decode()
        assert "NEXO" in page
        rama = urllib.request.urlopen(f"http://127.0.0.1:{port}/rama", timeout=3).read().decode()
        assert "Ramificación" in rama
        assert "NEXO_PRESENCE_TOKEN" in rama
    finally:
        httpd.shutdown()
        reset_presence_auth()
