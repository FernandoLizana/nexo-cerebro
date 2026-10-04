"""
Búsqueda ligera en YouTube (sin API key) para cuando Nexo elige ver algo en la TV.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request


def search(query: str, *, limit: int = 4) -> list[dict]:
    query = (query or "").strip()
    if not query:
        return []
    q = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={q}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "es,en;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return _invidious_fallback(query, limit=limit)

    ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
    seen: set[str] = set()
    results: list[dict] = []
    title_matches = re.findall(
        r'"title":\{"runs":\[\{"text":"((?:\\.|[^"\\])*)"\}\]', html
    )
    titles = [bytes(t, "utf-8").decode("unicode_escape") for t in title_matches]

    ti = 0
    for vid in ids:
        if vid in seen or vid == "undefined":
            continue
        seen.add(vid)
        title = titles[ti] if ti < len(titles) else query
        ti += 1
        results.append(
            {
                "video_id": vid,
                "title": title[:120],
                "url": f"https://www.youtube.com/watch?v={vid}",
            }
        )
        if len(results) >= limit:
            break
    if results:
        return results
    return _invidious_fallback(query, limit=limit)


def _invidious_fallback(query: str, *, limit: int) -> list[dict]:
    hosts = ["https://yewtu.be", "https://invidious.fdn.fr"]
    q = urllib.parse.quote(query)
    for host in hosts:
        try:
            api = f"{host}/api/v1/search?q={q}&type=video"
            req = urllib.request.Request(api, headers={"User-Agent": "cerebro/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            out = []
            for item in data[:limit]:
                if item.get("type") != "video":
                    continue
                vid = item.get("videoId") or item.get("video_id")
                if not vid:
                    continue
                out.append(
                    {
                        "video_id": vid,
                        "title": str(item.get("title", query))[:120],
                        "url": f"https://www.youtube.com/watch?v={vid}",
                    }
                )
            if out:
                return out
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, KeyError):
            continue
    return []
