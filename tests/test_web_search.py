"""Tests for web search helpers."""

from brain.web_search import _parse_ddg_lite, _parse_google_html, format_for_learning


def test_parse_ddg_lite_extracts_results():
    html = (
        '<a rel="nofollow" href="https://example.com/page">Ejemplo título</a>'
        '<td class="result-snippet">Un fragmento útil</td>'
        '<a rel="nofollow" href="https://duckduckgo.com/y.js">skip</a>'
        '<a rel="nofollow" href="https://other.org/x">Segundo</a>'
    )
    rows = _parse_ddg_lite(html, limit=5)
    assert len(rows) == 2
    assert rows[0]["title"] == "Ejemplo título"
    assert rows[0]["url"].startswith("https://example.com")
    assert "fragmento" in rows[0]["snippet"]


def test_parse_google_html_extracts_h3_links():
    html = (
        '<a href="/url?q=https%3A%2F%2Fwiki.org%2Fbrain"><h3>Cerebro humano</h3></a>'
        '<a href="/url?q=https%3A%2F%2Fwww.google.com">skip</a>'
    )
    rows = _parse_google_html(html, limit=3)
    assert len(rows) == 1
    assert "Cerebro" in rows[0]["title"]
    assert rows[0]["url"].startswith("https://wiki.org")


def test_format_for_learning():
    text = format_for_learning(
        {
            "provider": "duckduckgo",
            "query": "neurociencia",
            "results": [{"title": "Artículo", "url": "https://x", "snippet": "dato"}],
        }
    )
    assert "neurociencia" in text
    assert "Artículo" in text
