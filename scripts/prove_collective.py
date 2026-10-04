"""Live proof: four branches talk, a downloaded PDF is learned, capacity grows."""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

HUB = "http://127.0.0.1:8770"
CENTRAL = "http://127.0.0.1:5000"
PDFS = (
    "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
    "https://unec.edu.az/application/uploads/2014/12/pdf-sample.pdf",
    "https://pdfobject.com/pdf/sample.pdf",
)


def post(path: str, body: dict, base: str = HUB) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=8) as res:
        return json.loads(res.read().decode("utf-8"))


def get(path: str, base: str = HUB) -> dict:
    with urllib.request.urlopen(base + path, timeout=8) as res:
        return json.loads(res.read().decode("utf-8"))


def download_pdf() -> tuple[str, bytes, str]:
    from pypdf import PdfReader
    import io

    last = "no pdf"
    for url in PDFS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "nexo-proof"})
            with urllib.request.urlopen(req, timeout=25) as res:
                raw = res.read()
            text = "\n".join((page.extract_text() or "") for page in PdfReader(io.BytesIO(raw)).pages[:4])
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) >= 20:
                return url, raw, text
            last = f"short text from {url}"
        except Exception as exc:
            last = f"{url}: {exc}"
    raise SystemExit(last)


def labels(brain) -> list[str]:
    store = brain.hippocampus.store
    rows = store._db.execute("SELECT label FROM memories").fetchall()
    return [str(row[0] or "") for row in rows]


def main() -> int:
    url, raw, text = download_pdf()
    safe = text.encode("ascii", "replace").decode("ascii")
    print("pdf", url)
    print("text", safe[:180])

    for source, lesson in (
        ("rama", "el mango contiene vitamina c"),
        ("rama-b", "la ceiba da sombra ancha"),
        ("android-cerebro", "el telefono oye la casa"),
        ("android-nodo", "el nodo guarda el archivo"),
    ):
        greeted = post("/v1/interact", {"source": source, "kind": "GREET"})
        taught = post("/v1/interact", {"source": source, "kind": "TEACH", "text": lesson})
        assert greeted["ok"] and taught["ok"], source

    import base64

    uploaded = post(
        "/v1/material",
        {"source": "rama", "name": "internet.pdf", "data_b64": base64.b64encode(raw).decode("ascii")},
    )
    assert uploaded["ok"], uploaded
    paired = []
    for _ in range(3):
        row = post("/v1/pair", {})
        if row.get("ok"):
            paired.append(row)
    assert paired, "no pair"
    state = get("/v1/state")
    print("hub capacity", state["capacity"], "links", len(state["connections"]))
    print("pair", paired[0]["a"], "<->", paired[0]["b"])
    print("notebooks", {k: v[-1]["text"][:60] for k, v in state["notebooks"].items() if v})

    from brain import InfantApeBrain
    from brain.collective_capacity import apply_capacity, learn_offering
    from brain.experiment_flags import AblationFlags
    from brain.node_offerings import unread_offerings
    from brain.profile import COMPACT_PROFILE
    from brain.sleep_study import SleepStudyEngine
    from dataclasses import replace
    import tempfile

    held = next((row for row in unread_offerings() if str(row.get("name", "")).endswith(".pdf")), None)
    assert held, unread_offerings()
    excerpt = Path("data/node_shelf") / f"{held['id']}.txt"
    pdf_text = excerpt.read_text(encoding="utf-8")
    head = " ".join(pdf_text.split())[:90]
    token = next(
        word
        for word in re.findall(r"[A-Za-z]{6,}", head)
        if word.lower() not in {"dejado", "nodo", "simple", "sample", "document"}
    )
    print("token", token)
    assert token.lower() in pdf_text.lower()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        flags = replace(AblationFlags(), enable_sleep_study=True, enable_sleep_web=False)
        brain = InfantApeBrain(profile=COMPACT_PROFILE, state_dir=Path(tmp), experiment_flags=flags)
        brain.headless = True
        before = list(labels(brain))
        assert not any(token.lower() in row.lower() for row in before)
        grown = apply_capacity(brain, state)
        assert grown["wm_after"] > grown["wm_before"]
        item = {"id": held["id"], "source": "rama", "name": "internet.pdf", "text": pdf_text}
        learned = learn_offering(brain, item, via="curiosidad")
        import os
        from services.presence.shelf import accept

        sleep_shelf = Path(tmp) / "sleep_shelf"
        os.environ["NEXO_NODE_SHELF"] = str(sleep_shelf)
        accept("rama", "internet.pdf", raw)
        sleep = SleepStudyEngine()._study_nodes(brain, phase="rem", source="proof")
        os.environ.pop("NEXO_NODE_SHELF", None)
        after = labels(brain)
        hits = [row for row in after if token.lower() in row.lower()]
        print("wm", grown["wm_before"], "->", grown["wm_after"], "hippocampus", grown["hippocampus_after"])
        print("memory hit", hits[:2])
        print("phrase", learned["phrase"][:120])
        assert hits, "the pdf token never entered hippocampal labels"
        assert sleep or learned
    try:
        central = get("/api/collective", CENTRAL)
        print("live central", json.dumps(central, ensure_ascii=False)[:400])
    except Exception as exc:
        print("live central unread", exc)
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
