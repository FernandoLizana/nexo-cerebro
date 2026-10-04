"""Browser layer for NEXO Cognitive QA (P2)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nexo_qa.browser.models import (
    BrowserCommand,
    BrowserElementSnapshot,
    BrowserExecutionResult,
    BrowserSnapshot,
)
from nexo_qa.browser.policy import BrowserConfig, BrowserPolicy
from nexo_qa.browser.protocol import BrowserDriverProtocol

if TYPE_CHECKING:
    from nexo_qa.browser.browser_world import BrowserWorld
    from nexo_qa.browser.playwright_driver import PlaywrightDriver

__all__ = [
    "BrowserWorld",
    "BrowserDriverProtocol",
    "BrowserConfig",
    "BrowserPolicy",
    "BrowserSnapshot",
    "BrowserElementSnapshot",
    "BrowserCommand",
    "BrowserExecutionResult",
    "PlaywrightDriver",
]


def __getattr__(name: str):
    if name == "BrowserWorld":
        from nexo_qa.browser.browser_world import BrowserWorld

        return BrowserWorld
    if name == "PlaywrightDriver":
        from nexo_qa.browser.playwright_driver import PlaywrightDriver

        return PlaywrightDriver
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
