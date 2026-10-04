"""Privacy filters for BIP context — never ship private user conversations."""

from __future__ import annotations

import re
from typing import Any, Mapping


class PrivacyViolation(ValueError):
    """Context contains disallowed private-user fields."""


# Keys that look like private user chat / credentials — rejected hard.
FORBIDDEN_CONTEXT_KEYS: frozenset[str] = frozenset(
    {
        "user_chat",
        "private_chat",
        "user_message",
        "user_messages",
        "password",
        "passwd",
        "secret",
        "api_key",
        "token",
        "authorization",
        "cookie",
        "session",
        "clipboard",
        "browser_history",
        "keylog",
        "home_directory",
        "ssh_key",
    }
)

_FORBIDDEN_KEY_RE = re.compile(
    r"(user[_-]?chat|private[_-]?chat|password|api[_-]?key|secret|token|cookie|keylog|clipboard)",
    re.IGNORECASE,
)


def sanitize_interaction_context(context: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a cleaned context dict or raise PrivacyViolation.

    Only NEXO world metadata should appear here (raw_action, place tags, etc.).
    """
    raw = dict(context or {})
    clean: dict[str, Any] = {}
    for key, value in raw.items():
        key_s = str(key)
        key_l = key_s.lower()
        if key_l in FORBIDDEN_CONTEXT_KEYS or _FORBIDDEN_KEY_RE.search(key_s):
            raise PrivacyViolation(f"forbidden context key: {key_s}")
        if isinstance(value, str) and _looks_like_private_user_blob(value):
            raise PrivacyViolation(f"forbidden context value for key: {key_s}")
        if isinstance(value, dict):
            clean[key_s] = sanitize_interaction_context(value)
        elif isinstance(value, list):
            clean[key_s] = [_sanitize_item(v, key_s) for v in value]
        else:
            clean[key_s] = value
    return clean


def _sanitize_item(value: Any, parent_key: str) -> Any:
    if isinstance(value, dict):
        return sanitize_interaction_context(value)
    if isinstance(value, str) and _looks_like_private_user_blob(value):
        raise PrivacyViolation(f"forbidden context value for key: {parent_key}")
    return value


def _looks_like_private_user_blob(text: str) -> bool:
    lower = text.lower()
    markers = (
        "user said:",
        "private conversation",
        "-----begin private key-----",
        "password=",
        "authorization: bearer",
    )
    return any(m in lower for m in markers)
