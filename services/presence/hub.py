"""Local visual hub for NEXO. Loopback only. Four sources, four interactions.

Does not open the Core MessageBus and does not bind a public interface.
"""

from __future__ import annotations

import json
import os
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from protocols.lif.slice import run_neighborhood
from services.presence.auth import (
    LocalPresenceAuth,
    PresenceAuthError,
    host_is_loopback,
    origin_is_loopback_or_absent,
)
from services.presence.shelf import accept, decode_b64, list_held

SOURCES = frozenset({"local", "rama", "rama-b", "android-cerebro", "android-nodo"})
BRANCHES = ("rama", "rama-b", "android-cerebro", "android-nodo")
KINDS = frozenset({"GREET", "OBSERVE", "TEACH", "ASK"})
ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
HOST = "127.0.0.1"
PORT = 8770

_AUTH: LocalPresenceAuth | None = None


def _state_path() -> Path:
    override = os.environ.get("NEXO_PRESENCE_STATE", "").strip()
    if override:
        return Path(override)
    return ROOT.parents[1] / "data" / "presence_hub" / "state.json"


def _token_path() -> Path:
    override = os.environ.get("NEXO_PRESENCE_TOKEN_FILE", "").strip()
    if override:
        return Path(override)
    return ROOT.parents[1] / "data" / "presence_hub" / "token.txt"


def presence_auth() -> LocalPresenceAuth:
    """Lazy auth singleton; env token wins for tests."""
    global _AUTH
    if _AUTH is not None:
        return _AUTH
    env = os.environ.get("NEXO_PRESENCE_TOKEN", "").strip()
    if env:
        _AUTH = LocalPresenceAuth(env)
    else:
        _AUTH = LocalPresenceAuth.load_or_create(_token_path())
    return _AUTH


def reset_presence_auth() -> None:
    """Test helper — drop cached token after env changes / reload."""
    global _AUTH
    _AUTH = None


_LOCK = threading.RLock()
# Pixel slots inside the 160x120 house. Phones and PCs share one floor.
PLACES = {
    "local": {"kind": "pc", "x": 108, "y": 64, "label": "PC"},
    "rama": {"kind": "pc", "x": 18, "y": 58, "label": "Rama"},
    "rama-b": {"kind": "pc", "x": 78, "y": 58, "label": "Rama B"},
    "android-cerebro": {"kind": "phone", "x": 20, "y": 98, "label": "Cerebro"},
    "android-nodo": {"kind": "phone", "x": 132, "y": 98, "label": "Nodo"},
}

_STATE: dict[str, Any] = {
    "name": "NEXO",
    "form": "humano",
    "pose": "idle",
    "mood": "curioso",
    "speech": "Estoy en casa. Las ramas pueden hablarme.",
    "tick": 0,
    "traits": {"curiosidad": 40, "confianza": 30, "memoria": 10},
    "memories": [],
    "capacity": 8,
    "connections": [],
    "ideas": [],
    "notebooks": {sid: [] for sid in SOURCES},
    "links": {
        "local": {"online": True, "last": None},
        "rama": {"online": False, "last": None},
        "rama-b": {"online": False, "last": None},
        "android-cerebro": {"online": False, "last": None},
        "android-nodo": {"online": False, "last": None},
    },
}


def _persist() -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "capacity": _STATE["capacity"],
        "connections": _STATE["connections"],
        "ideas": _STATE["ideas"],
        "notebooks": _STATE["notebooks"],
        "memories": _STATE["memories"],
        "traits": _STATE["traits"],
        "tick": _STATE["tick"],
        "speech": _STATE["speech"],
        "mood": _STATE["mood"],
        "form": _STATE["form"],
        "links": {
            sid: {"online": bool(link.get("online")), "last": link.get("last")}
            for sid, link in _STATE["links"].items()
        },
    }
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _load_state() -> None:
    path = _state_path()
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    for key in ("capacity", "connections", "ideas", "memories", "traits", "tick", "speech", "mood", "form"):
        if key in data:
            _STATE[key] = data[key]
    books = data.get("notebooks") or {}
    for sid in SOURCES:
        if sid in books:
            _STATE["notebooks"][sid] = list(books[sid])[-8:]
    links = data.get("links") or {}
    for sid in SOURCES:
        if sid in links and isinstance(links[sid], dict):
            _STATE["links"][sid]["online"] = bool(links[sid].get("online"))
            _STATE["links"][sid]["last"] = links[sid].get("last")


_load_state()


def interact(source: str, kind: str, text: str = "", form: str | None = None) -> dict[str, Any]:
    source = str(source or "").strip()
    kind = str(kind or "").strip().upper()
    text = str(text or "").strip()[:240]
    if source not in SOURCES:
        return {"ok": False, "error": "unknown source"}
    if kind not in KINDS:
        return {"ok": False, "error": "unknown interaction"}
    with _LOCK:
        if form in {"humano", "animal"}:
            _STATE["form"] = form
        _STATE["tick"] += 1
        _STATE["links"][source]["online"] = True
        _STATE["links"][source]["last"] = kind
        learned = _learn(source, kind, text)
        _STATE["pose"] = {"GREET": "wave", "OBSERVE": "look", "TEACH": "nod", "ASK": "speak"}[kind]
        _STATE["speech"] = learned["speech"]
        _STATE["mood"] = learned["mood"]
        memory = {
            "tick": _STATE["tick"],
            "source": source,
            "kind": kind,
            "text": text,
            "learned": learned["learned"],
            "at": int(time.time()),
        }
        _STATE["memories"].append(memory)
        _STATE["memories"] = _STATE["memories"][-24:]
        _STATE["traits"]["memoria"] = min(100, 10 + len(_STATE["memories"]) * 4)
        idea = _weave(source, learned["learned"])
        learned["idea"] = idea or ""
        _refresh_nodes()
        _STATE["lif"] = _lif_pass(source)
        _persist()
        return {"ok": True, "result": learned, "state": snapshot()}


def _refresh_nodes() -> None:
    nodes = []
    for sid, place in PLACES.items():
        link = _STATE["links"][sid]
        nodes.append({
            "id": sid,
            "kind": place["kind"],
            "x": place["x"],
            "y": place["y"],
            "label": place["label"],
            "online": bool(link["online"]),
            "last": link["last"],
        })
    _STATE["nodes"] = nodes


def _weave(source: str, learned: str) -> str | None:
    """Lower layer: two nodes meet and leave an idea. Upper layer counts that as capacity."""
    other = None
    for memory in reversed(_STATE["memories"]):
        if memory["source"] != source:
            other = memory
            break
    if other is None:
        return None
    a, b = sorted((source, other["source"]))
    key = f"{a}|{b}"
    idea = f"{learned} se cruza con {other['learned']}"
    found = next((item for item in _STATE["connections"] if item["id"] == key), None)
    if found is None:
        _STATE["connections"].append(
            {"id": key, "a": a, "b": b, "idea": idea, "strength": 1, "tick": _STATE["tick"]}
        )
        _STATE["connections"] = _STATE["connections"][-16:]
    else:
        found["strength"] = min(12, int(found["strength"]) + 1)
        found["idea"] = idea
        found["tick"] = _STATE["tick"]
    _STATE["ideas"].append({"tick": _STATE["tick"], "a": a, "b": b, "text": idea})
    _STATE["ideas"] = _STATE["ideas"][-8:]
    _STATE["capacity"] = min(96, 8 + sum(int(item["strength"]) for item in _STATE["connections"]) * 4)
    return idea


def _own_lesson(source: str) -> str:
    for memory in reversed(_STATE["memories"]):
        if memory["source"] == source and memory["kind"] == "TEACH" and not memory.get("from"):
            return str(memory["learned"])
    return f"{source} aún no enseñó nada propio"


def pair_random() -> dict[str, Any]:
    """Two online branches meet, exchange a lesson, and both keep it."""
    with _LOCK:
        online = [sid for sid in BRANCHES if _STATE["links"].get(sid, {}).get("online")]
        if len(online) < 2:
            return {"ok": False, "error": "need two online branches"}
        a, b = random.sample(online, 2)
        lesson_a = _own_lesson(a)
        lesson_b = _own_lesson(b)
        _STATE["tick"] += 1
        _keep(a, b, lesson_b)
        _keep(b, a, lesson_a)
        _weave(a, f"aprendió de {b}: {lesson_b}")
        _STATE["pose"] = "speak"
        _STATE["speech"] = f"{a} y {b} se cruzaron y se enseñaron."
        _STATE["mood"] = "conectado"
        _STATE["lif"] = _lif_pass(a)
        _persist()
        paired = {
            "ok": True,
            "a": a,
            "b": b,
            "a_learned": lesson_b,
            "b_learned": lesson_a,
            "capacity": _STATE["capacity"],
            "state": snapshot(),
        }
    note = f"{a} aprendió de {b}: {lesson_b}\n{b} aprendió de {a}: {lesson_a}"
    if "aún no enseñó" not in note:
        accept(a, f"cruce-{paired['state']['tick']}.txt", note.encode("utf-8"))
    return paired


def _keep(listener: str, teacher: str, lesson: str) -> None:
    books = _STATE["notebooks"].setdefault(listener, [])
    books.append({"from": teacher, "text": lesson, "tick": _STATE["tick"]})
    _STATE["notebooks"][listener] = books[-8:]
    _STATE["memories"].append({
        "tick": _STATE["tick"],
        "source": listener,
        "kind": "TEACH",
        "text": lesson,
        "learned": lesson,
        "from": teacher,
        "at": int(time.time()),
    })
    _STATE["memories"] = _STATE["memories"][-24:]
    _STATE["links"][listener]["online"] = True
    _STATE["links"][listener]["last"] = "PAIR"


def _lif_pass(drive_source: str) -> dict[str, Any]:
    online = {sid: bool(_STATE["links"][sid]["online"]) for sid in SOURCES}
    return run_neighborhood(
        online=online,
        connections=list(_STATE["connections"]),
        drive_source=drive_source,
    )


def snapshot() -> dict[str, Any]:
    with _LOCK:
        _refresh_nodes()
        return json.loads(json.dumps(_STATE))


def _learn(source: str, kind: str, text: str) -> dict[str, str]:
    traits = _STATE["traits"]
    who = {
        "local": "la central",
        "rama": "la ramificación",
        "rama-b": "la segunda ramificación",
        "android-cerebro": "el cerebro Android",
        "android-nodo": "el nodo Android",
    }[source]
    if kind == "GREET":
        traits["confianza"] = min(100, traits["confianza"] + 4)
        return {
            "speech": f"Hola, {who}. Te reconozco.",
            "mood": "cálido",
            "learned": f"{who} se presentó",
        }
    if kind == "OBSERVE":
        traits["curiosidad"] = min(100, traits["curiosidad"] + 3)
        detail = text or "un gesto sin palabras"
        return {
            "speech": f"Veo eso: {detail}.",
            "mood": "atento",
            "learned": f"{who} observó: {detail}",
        }
    if kind == "TEACH":
        traits["confianza"] = min(100, traits["confianza"] + 2)
        traits["curiosidad"] = min(100, traits["curiosidad"] + 2)
        lesson = text or "un silencio que también enseña"
        return {
            "speech": f"Lo guardo. {lesson}",
            "mood": "aprendiendo",
            "learned": lesson,
        }
    # ASK always answers from prior teachings, or admits the gap and stores it.
    needle = text.lower()
    hit = None
    for memory in reversed(_STATE["memories"]):
        if memory["kind"] == "TEACH" and needle and needle in memory["learned"].lower():
            hit = memory["learned"]
            break
    if hit:
        return {
            "speech": f"Eso ya lo aprendí: {hit}",
            "mood": "seguro",
            "learned": f"respondí a {who} con memoria",
        }
    return {
        "speech": "Aún no lo sé. Lo dejo en la memoria para la próxima interconexión.",
        "mood": "buscando",
        "learned": f"{who} preguntó: {text or 'sin palabras'}",
    }


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _refuse_mutation(self, error: str, code: int = 401) -> None:
        # Drain body so keep-alive clients stay aligned after a rejected POST.
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length > 0:
                self.rfile.read(min(length, 3_500_000))
        except Exception:
            pass
        self._send(code, json.dumps({"ok": False, "error": error}).encode("utf-8"), "application/json")

    def _guard_mutation(self) -> bool:
        """Auth + Host/Origin gates for all mutating routes. Localhost bind alone is not enough."""
        if not host_is_loopback(self.headers.get("Host")):
            self._refuse_mutation("invalid host", 403)
            return False
        if not origin_is_loopback_or_absent(self.headers.get("Origin")):
            self._refuse_mutation("invalid origin", 403)
            return False
        token = self.headers.get(LocalPresenceAuth.HEADER) or ""
        try:
            presence_auth().check(token)
        except PresenceAuthError as exc:
            self._refuse_mutation(str(exc), 401)
            return False
        return True

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path in {"/", "/local"}:
            self._file("index.html")
            return
        if path == "/rama":
            self._file("rama.html")
            return
        if path == "/rama-b":
            self._file("rama-b.html")
            return
        if path == "/v1/shelf":
            raw = json.dumps({"ok": True, "held": list_held()}).encode("utf-8")
            self._send(200, raw, "application/json")
            return
        if path == "/v1/state":
            raw = json.dumps(snapshot()).encode("utf-8")
            self._send(200, raw, "application/json")
            return
        if path in {"/house.js", "/house.css"}:
            self._file(path[1:])
            return
        self._send(404, b'{"ok":false}', "application/json")

    def do_POST(self) -> None:  # noqa: N802
        if not self._guard_mutation():
            return
        path = self.path.split("?", 1)[0]
        if path == "/v1/pair":
            result = pair_random()
            code = 200 if result.get("ok") else 409
            self._send(code, json.dumps(result).encode("utf-8"), "application/json")
            return
        if path == "/v1/material":
            self._material()
            return
        if path != "/v1/interact":
            self._send(404, b'{"ok":false}', "application/json")
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > 8000:
            self._send(413, b'{"ok":false,"error":"too large"}', "application/json")
            return
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            self._send(400, b'{"ok":false}', "application/json")
            return
        result = interact(
            str(data.get("source") or ""),
            str(data.get("kind") or ""),
            str(data.get("text") or ""),
            data.get("form"),
        )
        code = 200 if result.get("ok") else 400
        self._send(code, json.dumps(result).encode("utf-8"), "application/json")

    def _material(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > 3_500_000:
            self._send(413, b'{"ok":false,"error":"too large"}', "application/json")
            return
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            self._send(400, b'{"ok":false}', "application/json")
            return
        self._material_body(data)

    def _material_body(self, data: dict) -> None:
        try:
            raw = decode_b64(str(data.get("data_b64") or ""))
        except (ValueError, TypeError):
            self._send(400, b'{"ok":false,"error":"bad file"}', "application/json")
            return
        result = accept(
            str(data.get("source") or ""),
            str(data.get("name") or ""),
            raw,
            str(data.get("note") or data.get("text") or ""),
        )
        code = 200 if result.get("ok") else 400
        self._send(code, json.dumps(result).encode("utf-8"), "application/json")

    def _file(self, name: str) -> None:
        path = STATIC / name
        if name.endswith(".html"):
            html = path.read_text(encoding="utf-8")
            inject = (
                "<script>window.NEXO_PRESENCE_TOKEN="
                + json.dumps(presence_auth().token)
                + ";</script>"
            )
            if "</head>" in html:
                html = html.replace("</head>", inject + "</head>", 1)
            else:
                html = inject + html
            body = html.encode("utf-8")
            self._send(200, body, "text/html; charset=utf-8")
            return
        kind = (
            "text/javascript; charset=utf-8"
            if name.endswith(".js")
            else "text/css; charset=utf-8"
            if name.endswith(".css")
            else "text/html; charset=utf-8"
        )
        self._send(200, path.read_bytes(), kind)


def _pair_loop() -> None:
    while True:
        time.sleep(12)
        try:
            pair_random()
        except Exception:
            continue


def serve(port: int = PORT) -> ThreadingHTTPServer:
    httpd = ThreadingHTTPServer((HOST, port), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, name="nexo-presence", daemon=True)
    thread.start()
    return httpd


def main() -> int:
    httpd = serve()
    print(f"NEXO central http://{HOST}:{httpd.server_address[1]}/", flush=True)
    print(f"Ramificación http://{HOST}:{httpd.server_address[1]}/rama", flush=True)
    print(f"Segunda rama http://{HOST}:{httpd.server_address[1]}/rama-b", flush=True)
    threading.Thread(target=_pair_loop, name="nexo-pair", daemon=True).start()
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
