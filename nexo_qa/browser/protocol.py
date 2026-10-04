"""Browser driver boundary — below EnvironmentProtocol, above Playwright."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from nexo_qa.browser.models import BrowserCommand, BrowserExecutionResult, BrowserSnapshot


@runtime_checkable
class BrowserDriverProtocol(Protocol):
    def start(self) -> None:
        ...

    def navigate(self, url: str) -> None:
        ...

    def snapshot(self) -> BrowserSnapshot:
        ...

    def execute(self, command: BrowserCommand) -> BrowserExecutionResult:
        ...

    def close(self) -> None:
        ...
