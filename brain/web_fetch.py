"""Fetch ligero de páginas web para aprendizaje autónomo."""

from __future__ import annotations

import re
import urllib.error
import urllib.parse
import urllib.request

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_page_text(url: str, *, max_chars: int = 2400) -> str:
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        return ""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read(120_000)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return ""
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        return ""
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]
