"""Browser security policy — allowlist and blocked capabilities.

Uses structured scheme/host/port checks. Prefix matching is intentionally
absent so hosts like localhost.attacker.invalid cannot slip through.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse

from nexo_qa.perception.config import PerceptionConfig


DEFAULT_ALLOWED_ORIGINS = (
    "http://127.0.0.1:*",
    "http://localhost:*",
)

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def _host_port(netloc: str) -> tuple[str, str | None]:
    host = netloc.strip().lower()
    if host.startswith("[") and "]" in host:
        end = host.index("]")
        name = host[1:end]
        rest = host[end + 1 :]
        port = rest[1:] if rest.startswith(":") and rest[1:] else None
        return name, port
    if host.count(":") == 1 and not host.startswith("["):
        name, port = host.split(":", 1)
        return name, port or None
    return host, None


def _pattern_parts(pattern: str) -> tuple[str, str, str | None]:
    """Return scheme, host, optional port (None = any)."""
    parsed = urlparse(pattern.replace(":*", ""))
    scheme = (parsed.scheme or "http").lower()
    host, port = _host_port(parsed.netloc or "")
    if pattern.rstrip("/").endswith(":*") or ":*" in pattern:
        port = None
    return scheme, host, port


@dataclass
class BrowserPolicy:
    allowed_origins: tuple[str, ...] = DEFAULT_ALLOWED_ORIGINS
    downloads_enabled: bool = False
    file_upload_enabled: bool = False
    external_navigation_blocked: bool = True

    def is_allowed_url(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if "@" in (parsed.netloc or ""):
            return False
        host, port = _host_port(parsed.netloc or "")
        if not host:
            return False
        for pattern in self.allowed_origins:
            scheme, allowed_host, allowed_port = _pattern_parts(pattern)
            if parsed.scheme.lower() != scheme:
                continue
            if host != allowed_host:
                continue
            if allowed_port is None:
                return True
            if port == allowed_port:
                return True
            if port is None and allowed_port in {"80", "443"}:
                return True
        return False

    def block_reason(self, url: str) -> str:
        if not self.is_allowed_url(url):
            return "POLICY_BLOCKED"
        return ""


@dataclass
class BrowserConfig:
    driver: str = "playwright"
    browser: str = "chromium"
    headless: bool = True
    navigation_timeout_ms: int = 10_000
    action_timeout_ms: int = 5_000
    viewport_width: int = 1280
    viewport_height: int = 720
    allowed_origins: tuple[str, ...] = DEFAULT_ALLOWED_ORIGINS
    screenshots_on_failure: bool = True
    screenshots_on_success: bool = False
    debug_capture_html: bool = False
    test_data: dict[str, str] = field(default_factory=dict)
    perception: PerceptionConfig = field(default_factory=PerceptionConfig)

    @classmethod
    def from_mapping(cls, data: dict) -> BrowserConfig:
        browser = dict(data.get("browser") or {})
        shots = dict(browser.get("screenshots") or {})
        perception_raw = dict(data.get("perception") or browser.get("perception") or {})
        return cls(
            driver=str(browser.get("driver", "playwright")),
            browser=str(browser.get("browser", "chromium")),
            headless=bool(browser.get("headless", True)),
            navigation_timeout_ms=int(browser.get("navigation_timeout_ms", 10_000)),
            action_timeout_ms=int(browser.get("action_timeout_ms", 5_000)),
            viewport_width=int(browser.get("viewport_width", 1280)),
            viewport_height=int(browser.get("viewport_height", 720)),
            allowed_origins=tuple(browser.get("allowed_origins", DEFAULT_ALLOWED_ORIGINS)),
            screenshots_on_failure=bool(shots.get("on_failure", True)),
            screenshots_on_success=bool(shots.get("on_success", False)),
            debug_capture_html=bool(browser.get("debug_capture_html", False)),
            test_data=dict(browser.get("test_data") or {}),
            perception=PerceptionConfig.from_mapping(perception_raw),
        )
