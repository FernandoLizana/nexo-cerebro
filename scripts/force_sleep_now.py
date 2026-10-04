"""Induce sleep + sleep study on running Nexo server."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5001"


def post(path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE}{path}", timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    post("/api/time", {"hour": 23, "minute": 20, "realtime": False, "time_scale": 10})
    print("Hora -> 23:20")
    out = post("/api/sleep/force", {"cycles": 2, "steps_per_cycle": 90})
    print(f"Durmió: replays={out.get('replays')} study={out.get('sleep_study', {}).get('count')}")
    hist = get("/api/sleep-study/history")
    for e in hist.get("sleep_study", {}).get("entries", [])[:8]:
        print(f"  · {e.get('label', e.get('title'))}")
    for _ in range(6):
        post("/api/world/tick", {"steps": 1})
    print("Listo — observatorio actualizado.")


if __name__ == "__main__":
    main()
