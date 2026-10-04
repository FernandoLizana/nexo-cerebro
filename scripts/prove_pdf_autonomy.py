"""Live proof: curiosity takes a PDF, then faint stores a phrase from the file body."""

from __future__ import annotations

import base64
import io
import json
import urllib.request

HUB = "http://127.0.0.1:8770"
CENTRAL = "http://127.0.0.1:5000"
PDF_URL = "https://unec.edu.az/application/uploads/2014/12/pdf-sample.pdf"


def post(url: str, body: dict, timeout: int) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8"))


def get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=20) as res:
        return json.loads(res.read().decode("utf-8"))


def main() -> int:
    from pypdf import PdfReader

    raw = urllib.request.urlopen(urllib.request.Request(PDF_URL, headers={"User-Agent": "nexo-proof"}), timeout=25).read()
    text = "\n".join((page.extract_text() or "") for page in PdfReader(io.BytesIO(raw)).pages[:2])
    print("pdf chars", len(text))
    blob = base64.b64encode(raw).decode("ascii")
    post(f"{CENTRAL}/api/time", {"hour": 14, "minute": 0, "realtime": False, "paused": False}, 20)
    first = post(f"{HUB}/v1/material", {"source": "rama", "name": "curiosity.pdf", "data_b64": blob}, 20)
    print("shelf", first.get("ok"), first.get("item", {}).get("id"))
    post(f"{CENTRAL}/api/world/tick", {"steps": 1}, 90)
    notice = get(f"{CENTRAL}/api/collective")
    print("autonomy", json.dumps(notice.get("notice"), ensure_ascii=False)[:500])
    studied = (notice.get("notice") or {}).get("studied") or ""
    reason = (notice.get("notice") or {}).get("reason")
    assert reason in {"curiosity", "sleep"}, notice
    assert studied and "dejado" not in studied.lower()
    assert any(word.lower() in text.lower() for word in studied.split()[:4]), studied

    second = post(f"{HUB}/v1/material", {"source": "rama-b", "name": "faint.pdf", "data_b64": blob}, 20)
    assert second.get("ok")
    faint = post(f"{CENTRAL}/api/faint", {}, 180)
    print("faint", json.dumps({k: faint.get(k) for k in ("learned", "phrase", "recall", "message")}, ensure_ascii=False)[:600])
    token = (faint.get("recall") or {}).get("token") or ""
    assert faint.get("learned") is True
    assert token.lower() not in {"colibri", "ixora", "dejado"}
    assert token.lower() in text.lower()
    print("OK", reason, token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
