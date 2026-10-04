"""Browser-layer DTOs — serializable, no Playwright handles."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

CommandType = Literal["CLICK", "FOCUS", "TYPE", "SELECT", "TOGGLE", "SCROLL", "BACK", "NAVIGATE"]


@dataclass(frozen=True, slots=True)
class BrowserElementSnapshot:
    element_id: str
    role: str
    visible_text: str
    tag: str
    enabled: bool
    editable: bool
    checked: bool | None = None
    selected: bool | None = None
    bounding_box: tuple[float, float, float, float] | None = None
    visibility: float = 1.0
    semantic_hint: str = ""
    input_type: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "element_id": self.element_id,
            "role": self.role,
            "visible_text": self.visible_text,
            "tag": self.tag,
            "enabled": self.enabled,
            "editable": self.editable,
            "checked": self.checked,
            "selected": self.selected,
            "bounding_box": self.bounding_box,
            "visibility": self.visibility,
            "semantic_hint": self.semantic_hint,
            "input_type": self.input_type,
        }


@dataclass(frozen=True, slots=True)
class BrowserSnapshot:
    url: str
    title: str
    visible_elements: tuple[BrowserElementSnapshot, ...]
    focused_element: str | None = None
    viewport: tuple[int, int] = (1280, 720)
    timestamp: float = 0.0
    document_state: str = "loaded"
    scroll_position: tuple[float, float] = (0.0, 0.0)
    element_meta: dict[str, dict[str, Any]] = field(default_factory=dict)
    perception_mode: str = "dom_fast"

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "visible_elements": [e.to_dict() for e in self.visible_elements],
            "focused_element": self.focused_element,
            "viewport": list(self.viewport),
            "timestamp": self.timestamp,
            "document_state": self.document_state,
            "scroll_position": list(self.scroll_position),
            "perception_mode": self.perception_mode,
        }


@dataclass(frozen=True, slots=True)
class BrowserCommand:
    command_type: CommandType
    element_id: str | None = None
    text: str | None = None
    url: str | None = None
    scroll_direction: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "command_type": self.command_type,
            "element_id": self.element_id,
            "text": self.text,
            "url": self.url,
            "scroll_direction": self.scroll_direction,
        }


@dataclass(frozen=True, slots=True)
class BrowserExecutionResult:
    executed: bool
    failed: bool
    timeout: bool = False
    navigation_occurred: bool = False
    dom_changed: bool = False
    url_changed: bool = False
    error_type: str | None = None
    error_message: str | None = None
    duration_ms: float = 0.0
    url_after: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "executed": self.executed,
            "failed": self.failed,
            "timeout": self.timeout,
            "navigation_occurred": self.navigation_occurred,
            "dom_changed": self.dom_changed,
            "url_changed": self.url_changed,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "url_after": self.url_after,
        }
