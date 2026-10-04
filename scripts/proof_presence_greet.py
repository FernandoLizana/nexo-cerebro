#!/usr/bin/env python3
"""HTTP smoke for presence hub: unauthorized blocked, authorized GREET ok.

Reads token from data/presence_hub/token.txt or NEXO_PRESENCE_TOKEN.
Never prints the token value.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _token() -> str:
    env = os.environ.get("NEXO_PRESENCE_TOKEN", "").strip()
    if env:
        return env
    path = ROOT / "data" / "presence_hub" / "token.txt"
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    raise SystemExit("missing presence token (file or NEXO_PRESENCE_TOKEN)")


def _post(path: str, body: dict, *, token: str | None, host: str) -> tuple[int, dict]:
    import http.client

    raw = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json", "Host": host, "Content-Length": str(len(raw))}
    if token:
        headers["X-Nexo-Presence-Token"] = token
    conn = http.client.HTTPConnection("127.0.0.1", 8770, timeout=5)
    try:
        conn.request("POST", path, body=raw, headers=headers)
        res = conn.getresponse()
        payload = res.read().decode("utf-8")
        try:
            data = json.loads(payload) if payload else {}
        except json.JSONDecodeError:
            data = {"raw": payload[:200]}
        return int(res.status), data
    finally:
        conn.close()


def main() -> int:
    tok = _token()
    body = {"source": "android-cerebro", "kind": "GREET", "text": "hola prueba auto"}
    code_no, _ = _post("/v1/interact", body, token=None, host="127.0.0.1:8770")
    if code_no not in (401, 403):
        print(json.dumps({"ok": False, "error": "expected_401", "got": code_no}))
        return 1
    code_ok, data = _post(
        "/v1/interact",
        body,
        token=tok,
        host="10.0.2.2:8770",  # emulator lab Host alias
    )
    if code_ok != 200:
        print(json.dumps({"ok": False, "error": "auth_post_failed", "got": code_ok, "body_keys": list(data)[:8]}))
        return 1
    state = json.loads(
        urllib.request.urlopen("http://127.0.0.1:8770/v1/state", timeout=3).read().decode()
    )
    links = state.get("links") or {}
    android = links.get("android-cerebro") or {}
    print(
        json.dumps(
            {
                "ok": True,
                "unauthorized": code_no,
                "authorized": code_ok,
                "android_cerebro_online": bool(android.get("online")),
                "tick": state.get("tick"),
                "capacity": state.get("capacity"),
            },
            ensure_ascii=True,
        )
    )
    return 0 if android.get("online") else 2


if __name__ == "__main__":
    raise SystemExit(main())
