"""Prove remaining MUST items against the live hub and central."""

from __future__ import annotations

import base64
import json
import time
import urllib.request

HUB = "http://127.0.0.1:8770"
CENTRAL = "http://127.0.0.1:5000"


def post(url: str, body: dict, timeout: int = 20) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8"))


def get(url: str, timeout: int = 20) -> dict | str:
    with urllib.request.urlopen(url, timeout=timeout) as res:
        raw = res.read().decode("utf-8")
        if "json" in (res.headers.get("Content-Type") or ""):
            return json.loads(raw)
        return raw


def main() -> int:
    # Capacity: not connectome, real WM retention
    col = get(f"{CENTRAL}/api/collective")
    assert isinstance(col, dict)
    assert col.get("not_connectome") is True
    assert col.get("metric") == "working_memory_and_hippocampus"
    print("capacity", col.get("wm"), "hippocampus", col.get("hippocampus"), "retention", col.get("retention"))

    # Teach from all four branch sources (PC + Android identity)
    lessons = {
        "rama": "la rama pc guarda el puma andino",
        "rama-b": "la rama b guarda el guanaco del norte",
        "android-cerebro": "el cerebro android guarda el quilombo quieto",
        "android-nodo": "el nodo android guarda la quiltra fiel",
    }
    for source, lesson in lessons.items():
        assert post(f"{HUB}/v1/interact", {"source": source, "kind": "TEACH", "text": lesson})["ok"]

    pdf = b"%PDF-1.1\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\nAdobe Acrobat PDF Files Portable Document Format\n"
    assert post(
        f"{HUB}/v1/material",
        {
            "source": "android-nodo",
            "name": "nodo.pdf",
            "data_b64": base64.b64encode(pdf).decode("ascii"),
            "note": "",
        },
    )["ok"]

    before = get(f"{HUB}/v1/state")
    assert isinstance(before, dict)
    tick0 = int(before.get("tick") or 0)
    print("waiting for automatic pair…")
    paired = False
    for _ in range(20):
        time.sleep(2)
        now = get(f"{HUB}/v1/state")
        assert isinstance(now, dict)
        if int(now.get("tick") or 0) > tick0 and now.get("speech", "").find("se cruzaron") >= 0:
            paired = True
            print("auto-pair", now.get("speech"), "capacity", now.get("capacity"))
            books = now.get("notebooks") or {}
            assert any(books.get(sid) for sid in lessons)
            break
    assert paired, "background pair loop did not fire"

    # Branch UI contract strings present
    rama = get(f"{HUB}/rama")
    rama_b = get(f"{HUB}/rama-b")
    assert isinstance(rama, str) and 'id="peers"' in rama
    assert isinstance(rama_b, str) and 'id="peers"' in rama_b
    house = get(f"{HUB}/house.js")
    assert isinstance(house, str) and "aprendió de" in house

    # 3D surface: Desmayo + GLTF loader + procedural fallback
    page = get(f"{CENTRAL}/")
    assert isinstance(page, str)
    assert "btn-faint" in page or "Desmayo" in page
    assert "GLTFLoader" in page
    blender = get(f"{CENTRAL}/api/world3d/blender")
    assert isinstance(blender, dict) and blender.get("present") is False
    print("3d ok procedural, faint button present")

    # Tick central so capacity applies after links
    post(f"{CENTRAL}/api/world/tick", {"steps": 1}, timeout=90)
    after = get(f"{CENTRAL}/api/collective")
    assert isinstance(after, dict)
    print("central after links", json.dumps({k: after.get(k) for k in ("wm", "hippocampus", "links", "retention", "not_connectome")}, ensure_ascii=False))
    assert after.get("not_connectome") is True
    if after.get("links", 0) > 0:
        assert after["wm"] > 7 or after["retention"]["ok"]
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
