"""Capture README stills and a short tour from a local observatory and presence hub.

Uses an already running demo. Does not print tokens. Writes under docs/media/.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "media"
OBS = os.environ.get("NEXO_OBS_URL", "http://127.0.0.1:5055/")
HUB = os.environ.get("NEXO_HUB_URL", "http://127.0.0.1:8770/")
SECTIONS = ("observatorio", "constelacion", "memoria", "laboratorio", "conexiones")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault(
        "PLAYWRIGHT_BROWSERS_PATH",
        str(Path.home() / "AppData" / "Local" / "ms-playwright"),
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.goto(OBS, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2500)
        title = page.title()
        if "NEXO" not in title:
            print(f"refusing capture: unexpected title {title!r}", file=sys.stderr)
            context.close()
            browser.close()
            return 1
        page.evaluate(
            """() => {
              for (const el of document.querySelectorAll('.badge')) {
                if (/gpu|nvidia/i.test(el.textContent || '')) el.remove();
              }
            }"""
        )
        for name in SECTIONS:
            page.click(f'button[data-section="{name}"]')
            page.wait_for_timeout(1200)
            section = page.locator(f"#section-{name}")
            section.scroll_into_view_if_needed()
            page.wait_for_timeout(400)
            section.screenshot(path=str(OUT / f"{name}.png"))
        page.goto(HUB, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT / "hub.png"))
        for name in ("rama", "rama-b"):
            page.goto(HUB.rstrip("/") + "/" + name, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(1200)
            page.screenshot(path=str(OUT / f"{name}.png"))
        context.close()
        browser.close()
    print(f"stills={OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
