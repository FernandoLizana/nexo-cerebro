"""
Búsqueda web para Nexo — Google (API opcional) o DuckDuckGo sin clave.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from html import unescape

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def search(query: str, *, limit: int = 5) -> dict:
    """Devuelve {provider, query, results: [{title, url, snippet}]}."""
    query = (query or "").strip()
    if not query:
        return {"provider": "none", "query": "", "results": []}

    limit = max(1, min(limit, 8))
    api_key = os.environ.get("CEREBRO_GOOGLE_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    cse_id = os.environ.get("CEREBRO_GOOGLE_CSE_ID") or os.environ.get("GOOGLE_CSE_ID")
    if api_key and cse_id:
        results = _google_cse(query, api_key=api_key, cse_id=cse_id, limit=limit)
        if results:
            return {"provider": "google", "query": query, "results": results}

    results = _duckduckgo_lite(query, limit=limit)
    if results:
        return {"provider": "duckduckgo", "query": query, "results": results}

    results = _google_html(query, limit=limit)
    if results:
        return {"provider": "google", "query": query, "results": results}

    return {"provider": "none", "query": query, "results": []}


def format_for_learning(payload: dict) -> str:
    q = payload.get("query", "")
    prov = payload.get("provider", "web")
    lines = [f"Búsqueda ({prov}): {q}"]
    for r in payload.get("results", [])[:4]:
        snip = (r.get("snippet") or "")[:140]
        lines.append(f"• {r.get('title', '?')[:90]}")
        if snip:
            lines.append(f"  {snip}")
        lines.append(f"  {r.get('url', '')[:120]}")
    return "\n".join(lines)[:1800]


def _google_cse(query: str, *, api_key: str, cse_id: str, limit: int) -> list[dict]:
    params = urllib.parse.urlencode(
        {"key": api_key, "cx": cse_id, "q": query, "num": min(limit, 10)}
    )
    url = f"https://www.googleapis.com/customsearch/v1?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, KeyError):
        return []
    out: list[dict] = []
    for item in data.get("items", [])[:limit]:
        out.append(
            {
                "title": str(item.get("title", ""))[:120],
                "url": str(item.get("link", ""))[:240],
                "snippet": str(item.get("snippet", ""))[:240],
            }
        )
    return out


def _duckduckgo_lite(query: str, *, limit: int) -> list[dict]:
    q = urllib.parse.quote(query)
    url = f"https://lite.duckduckgo.com/lite/?q={q}"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": _USER_AGENT, "Accept-Language": "es,en;q=0.8"},
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return []
    return _parse_ddg_lite(html, limit=limit)


def _parse_ddg_lite(html: str, *, limit: int) -> list[dict]:
    results: list[dict] = []
    rows = re.findall(
        r'<a[^>]+rel="nofollow"[^>]+href="(https?://[^"]+)"[^>]*>([^<]+)</a>',
        html,
        flags=re.I,
    )
    snippets = re.findall(
        r'<td[^>]*class="result-snippet"[^>]*>([^<]+(?:<[^>]+>[^<]*)*)</td>',
        html,
        flags=re.I,
    )
    seen: set[str] = set()
    si = 0
    for href, title in rows:
        if "duckduckgo.com" in href:
            continue
        if href in seen:
            continue
        seen.add(href)
        snip = ""
        if si < len(snippets):
            snip = re.sub(r"<[^>]+>", "", snippets[si]).strip()
            si += 1
        results.append(
            {
                "title": unescape(title.strip())[:120],
                "url": href[:240],
                "snippet": unescape(snip)[:240],
            }
        )
        if len(results) >= limit:
            break
    return results


def _google_html(query: str, *, limit: int) -> list[dict]:
    q = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={q}&hl=es&num={limit + 2}"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": _USER_AGENT, "Accept-Language": "es,en;q=0.8"},
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return []
    return _parse_google_html(html, limit=limit)


def _parse_google_html(html: str, *, limit: int) -> list[dict]:
    results: list[dict] = []
    seen: set[str] = set()
    for m in re.finditer(r'<a href="/url\?q=([^&"]+)[^"]*"[^>]*><h3[^>]*>(.*?)</h3>', html, re.I | re.S):
        href = urllib.parse.unquote(m.group(1))
        if not href.startswith("http") or "google.com" in href or href in seen:
            continue
        title = re.sub(r"<[^>]+>", "", m.group(2))
        title = unescape(title.strip())
        if not title:
            continue
        seen.add(href)
        results.append({"title": title[:120], "url": href[:240], "snippet": ""})
        if len(results) >= limit:
            break
    if results:
        return results
    for m in re.finditer(r'<a[^>]+href="(https?://(?!www\.google)[^"]+)"[^>]*>([^<]{4,120})</a>', html):
        href, title = m.group(1), unescape(m.group(2).strip())
        if href in seen or "google" in href:
            continue
        seen.add(href)
        results.append({"title": title[:120], "url": href[:240], "snippet": ""})
        if len(results) >= limit:
            break
    return results
