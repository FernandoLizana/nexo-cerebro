"""Playwright sync driver — encapsulates Chromium, no cognition."""

from __future__ import annotations

import time
from typing import Any

from nexo_qa.browser.models import BrowserCommand, BrowserElementSnapshot, BrowserExecutionResult, BrowserSnapshot
from nexo_qa.browser.policy import BrowserConfig, BrowserPolicy


class PlaywrightDriver:
    """Low-level browser automation. Not imported by nexo core."""

    def __init__(
        self,
        *,
        config: BrowserConfig | None = None,
        policy: BrowserPolicy | None = None,
    ) -> None:
        self.config = config or BrowserConfig()
        self.policy = policy or BrowserPolicy(allowed_origins=self.config.allowed_origins)
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self._page: Any = None
        self._element_locators: dict[str, dict[str, str]] = {}
        self._last_url: str = ""

    def start(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise ImportError(
                "Playwright is required for BrowserWorld. Install with: "
                "pip install -e '.[browser]' && playwright install chromium"
            ) from exc
        self._playwright = sync_playwright().start()
        launcher = getattr(self._playwright, self.config.browser, self._playwright.chromium)
        # Explicit launch budget: avoid indefinite hang when Chromium is starved.
        launch_timeout_ms = max(self.config.navigation_timeout_ms * 4, 60_000)
        try:
            self._browser = launcher.launch(
                headless=self.config.headless,
                timeout=launch_timeout_ms,
            )
            self._context = self._browser.new_context(
                viewport={"width": self.config.viewport_width, "height": self.config.viewport_height},
                accept_downloads=self.policy.downloads_enabled,
            )
            self._page = self._context.new_page()
        except Exception:
            self.close()
            raise
        self._page.set_default_timeout(self.config.action_timeout_ms)
        self._page.set_default_navigation_timeout(self.config.navigation_timeout_ms)

    def navigate(self, url: str) -> None:
        if not self.policy.is_allowed_url(url):
            raise PermissionError(f"POLICY_BLOCKED: navigation to {url!r} not allowed")
        assert self._page is not None
        self._page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=self.config.navigation_timeout_ms,
        )
        self._last_url = self._page.url

    def snapshot(self, *, mode: str | None = None) -> BrowserSnapshot:
        assert self._page is not None
        perception_mode = (mode or self.config.perception.mode or "dom_fast").lower()
        if perception_mode == "hybrid":
            raw = self._page.evaluate(_HYBRID_SCRIPT)
            raw_elements = raw.get("elements") or []
            scroll = raw.get("scroll") or [0, 0]
            focused_idx = None
        else:
            raw_elements = self._page.evaluate(_DOM_FAST_SCRIPT)
            scroll = [0, 0]
            focused_idx = None
        elements: list[BrowserElementSnapshot] = []
        element_meta: dict[str, dict[str, Any]] = {}
        self._element_locators.clear()
        active_element_id: str | None = None
        for idx, row in enumerate(raw_elements, start=1):
            element_id = f"web:e:{idx:04d}"
            bbox = row.get("bbox")
            box = tuple(bbox) if bbox and len(bbox) == 4 else None
            elements.append(
                BrowserElementSnapshot(
                    element_id=element_id,
                    role=str(row.get("role") or ""),
                    visible_text=str(row.get("text") or "")[:120],
                    tag=str(row.get("tag") or ""),
                    enabled=bool(row.get("enabled", True)),
                    editable=bool(row.get("editable", False)),
                    checked=row.get("checked"),
                    bounding_box=box,  # type: ignore[arg-type]
                    visibility=float(row.get("visibility", 1.0)),
                    semantic_hint=str(row.get("hint") or "")[:80],
                    input_type=str(row.get("inputType") or ""),
                )
            )
            self._element_locators[element_id] = dict(row.get("locator") or {})
            if row.get("isActive"):
                active_element_id = element_id
            if perception_mode == "hybrid":
                element_meta[element_id] = {
                    k: row.get(k)
                    for k in (
                        "occlusion",
                        "fg",
                        "bg",
                        "landmark",
                        "labelSource",
                        "sources",
                        "isModal",
                        "fontSize",
                        "fontWeight",
                    )
                    if row.get(k) is not None
                }
        title = self._page.title()
        focused_element = active_element_id or (elements[0].element_id if elements else None)
        return BrowserSnapshot(
            url=self._page.url,
            title=title,
            visible_elements=tuple(elements),
            focused_element=focused_element,
            viewport=(self.config.viewport_width, self.config.viewport_height),
            timestamp=time.time(),
            document_state="loaded",
            scroll_position=(float(scroll[0]), float(scroll[1])),
            element_meta=element_meta,
            perception_mode=perception_mode,
        )

    def execute(self, command: BrowserCommand) -> BrowserExecutionResult:
        assert self._page is not None
        t0 = time.perf_counter()
        url_before = self._page.url
        try:
            if command.command_type == "NAVIGATE":
                if command.url and not self.policy.is_allowed_url(command.url):
                    return self._result(
                        failed=True,
                        error_type="POLICY_BLOCKED",
                        error_message=f"blocked url {command.url}",
                        duration_ms=(time.perf_counter() - t0) * 1000,
                        url_after=url_before,
                    )
                if command.url:
                    self._page.goto(command.url, wait_until="domcontentloaded")
            elif command.command_type == "BACK":
                self._page.go_back(wait_until="domcontentloaded")
            elif command.command_type == "SCROLL":
                delta = 400 if command.scroll_direction != "up" else -400
                self._page.mouse.wheel(0, delta)
            elif command.command_type in ("CLICK", "FOCUS", "TYPE", "TOGGLE", "SELECT"):
                locator = self._resolve_locator(command.element_id)
                if locator is None:
                    return self._result(
                        failed=True,
                        error_type="ELEMENT_NO_LONGER_AVAILABLE",
                        error_message=f"missing element {command.element_id}",
                        duration_ms=(time.perf_counter() - t0) * 1000,
                        url_after=url_before,
                    )
                if command.command_type == "CLICK":
                    locator.click(timeout=self.config.action_timeout_ms)
                elif command.command_type == "FOCUS":
                    locator.focus(timeout=self.config.action_timeout_ms)
                elif command.command_type == "TYPE":
                    locator.fill(command.text or "", timeout=self.config.action_timeout_ms)
                elif command.command_type == "TOGGLE":
                    if not locator.is_checked():
                        locator.check(timeout=self.config.action_timeout_ms)
                    else:
                        locator.uncheck(timeout=self.config.action_timeout_ms)
                elif command.command_type == "SELECT":
                    locator.select_option(command.text or "", timeout=self.config.action_timeout_ms)
            else:
                return self._result(
                    failed=True,
                    error_type="UNSUPPORTED_COMMAND",
                    error_message=command.command_type,
                    duration_ms=(time.perf_counter() - t0) * 1000,
                    url_after=url_before,
                )
            self._page.wait_for_load_state("domcontentloaded", timeout=self.config.action_timeout_ms)
        except Exception as exc:  # noqa: BLE001 — normalize driver errors
            err = str(exc)
            error_type = "BROWSER_TIMEOUT" if "Timeout" in err else "ELEMENT_NOT_ACTIONABLE"
            return self._result(
                failed=True,
                timeout="Timeout" in err,
                error_type=error_type,
                error_message=err[:200],
                duration_ms=(time.perf_counter() - t0) * 1000,
                url_after=self._page.url,
            )
        url_after = self._page.url
        return self._result(
            executed=True,
            navigation_occurred=url_after != url_before,
            url_changed=url_after != url_before,
            dom_changed=True,
            duration_ms=(time.perf_counter() - t0) * 1000,
            url_after=url_after,
        )

    def close(self) -> None:
        # Snapshot refs then clear so re-entrant close is a no-op. Close the
        # browser FIRST: under load, context/page close can hang and previously
        # left chrome-headless-shell orphans that starved later matrix files
        # (P1-9: test_p5_personas flake after ~60 prior files).
        page = self._page
        context = self._context
        browser = self._browser
        playwright = self._playwright
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
        for closer in (
            (lambda: browser.close()) if browser is not None else None,
            (lambda: context.close()) if context is not None else None,
            (lambda: page.close()) if page is not None else None,
            (lambda: playwright.stop()) if playwright is not None else None,
        ):
            if closer is None:
                continue
            try:
                closer()
            except Exception:
                pass

    def _resolve_locator(self, element_id: str | None):
        if not element_id or self._page is None:
            return None
        spec = self._element_locators.get(element_id)
        if not spec:
            return None
        if spec.get("testid"):
            return self._page.get_by_test_id(spec["testid"])
        if spec.get("role") and spec.get("name"):
            return self._page.get_by_role(spec["role"], name=spec["name"])
        if spec.get("selector"):
            return self._page.locator(spec["selector"])
        return None

    @staticmethod
    def _result(**kwargs: Any) -> BrowserExecutionResult:
        return BrowserExecutionResult(
            executed=bool(kwargs.get("executed")),
            failed=bool(kwargs.get("failed")),
            timeout=bool(kwargs.get("timeout")),
            navigation_occurred=bool(kwargs.get("navigation_occurred")),
            dom_changed=bool(kwargs.get("dom_changed")),
            url_changed=bool(kwargs.get("url_changed")),
            error_type=kwargs.get("error_type"),
            error_message=kwargs.get("error_message"),
            duration_ms=float(kwargs.get("duration_ms", 0.0)),
            url_after=str(kwargs.get("url_after", "")),
        )


_DOM_FAST_SCRIPT = """
() => {
  const out = [];
  const isVisible = (el) => {
    if (!el || el.getAttribute('aria-hidden') === 'true') return false;
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  };
  const textOf = (el) => (el.innerText || el.getAttribute('aria-label') || el.getAttribute('placeholder') || el.value || '').trim();
  const push = (el, role, tag) => {
    if (!isVisible(el)) return;
    const testid = el.getAttribute('data-testid');
    const name = textOf(el);
    const locator = {};
    if (testid) locator.testid = testid;
    else if (role && name) { locator.role = role; locator.name = name; }
    else locator.selector = tag + (el.id ? '#' + el.id : '');
    const rect = el.getBoundingClientRect();
    out.push({
      role: role || tag,
      tag,
      text: name,
      hint: el.getAttribute('aria-label') || el.getAttribute('placeholder') || '',
      enabled: !el.disabled,
      editable: el.isContentEditable || tag === 'textarea' || tag === 'input',
      checked: el.checked,
      inputType: el.type || '',
      visibility: 1.0,
      bbox: [rect.x, rect.y, rect.width, rect.height],
      locator,
      isActive: document.activeElement === el,
    });
  };
  document.querySelectorAll('button, a, input, textarea, select, [role=\"button\"]').forEach((el) => {
    const tag = el.tagName.toLowerCase();
    let role = el.getAttribute('role') || tag;
    if (tag === 'input' && el.type === 'hidden') return;
    push(el, role, tag);
  });
  document.querySelectorAll('h1,h2,h3').forEach((el) => push(el, 'heading', el.tagName.toLowerCase()));
  return out.slice(0, 24);
}
"""

_HYBRID_SCRIPT = """
() => {
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const scroll = [window.scrollX || 0, window.scrollY || 0];
  const out = [];
  const parseRgb = (color) => {
    const m = /rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/.exec(color || '');
    if (!m) return [0.1, 0.1, 0.1];
    return [parseInt(m[1],10)/255, parseInt(m[2],10)/255, parseInt(m[3],10)/255];
  };
  const isVisible = (el) => {
    if (!el || el.getAttribute('aria-hidden') === 'true') return false;
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden' || parseFloat(style.opacity||'1') === 0) return false;
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  };
  const landmarkOf = (el) => {
    let cur = el;
    while (cur) {
      const tag = (cur.tagName||'').toLowerCase();
      const role = cur.getAttribute('role');
      if (tag === 'header' || role === 'banner') return 'header';
      if (tag === 'nav' || role === 'navigation') return 'navigation';
      if (tag === 'main' || role === 'main') return 'main';
      if (tag === 'footer' || role === 'contentinfo') return 'footer';
      if (role === 'dialog' || cur.classList?.contains('modal')) return 'modal';
      cur = cur.parentElement;
    }
    return 'main';
  };
  const occlusionAt = (el, rect) => {
    const cx = rect.x + rect.width / 2;
    const cy = rect.y + rect.height / 2;
    if (cx < 0 || cy < 0 || cx > vw || cy > vh) return 0;
    const top = document.elementFromPoint(cx, cy);
    if (!top) return 0;
    if (top === el || el.contains(top)) return 0;
    if (top.contains(el)) return 0;
    return 0.85;
  };
  const textOf = (el) => (el.innerText || el.getAttribute('aria-label') || el.getAttribute('placeholder') || el.value || '').trim();
  const labelSource = (el, name) => {
    if (el.innerText && el.innerText.trim()) return 'visible_text';
    if (el.getAttribute('aria-label')) return 'aria';
    if (el.getAttribute('placeholder')) return 'placeholder';
    const id = el.id;
    if (id) {
      const lab = document.querySelector(`label[for="${id}"]`);
      if (lab) return 'associated_label';
    }
    return name ? 'visible_text' : 'role';
  };
  const push = (el, role, tag) => {
    if (!isVisible(el)) return;
    const testid = el.getAttribute('data-testid');
    const name = textOf(el);
    const locator = {};
    if (testid) locator.testid = testid;
    else if (role && name) { locator.role = role; locator.name = name; }
    else locator.selector = tag + (el.id ? '#' + el.id : '');
    const rect = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    const fg = parseRgb(style.color);
    const bg = parseRgb(style.backgroundColor);
    const oc = occlusionAt(el, rect);
    const inter = rect.bottom > 0 && rect.top < vh && rect.right > 0 && rect.left < vw;
    let visibility = 1.0;
    if (!inter) visibility = 0.0;
    else {
      const visH = Math.min(rect.bottom, vh) - Math.max(rect.top, 0);
      const visW = Math.min(rect.right, vw) - Math.max(rect.left, 0);
      visibility = Math.min(1, Math.max(0, (visW * visH) / Math.max(1, rect.width * rect.height)));
    }
    const isModal = el.closest('[role=dialog],dialog,.modal-overlay,.modal') !== null
      || el.getAttribute('role') === 'alert';
    out.push({
      role: role || tag,
      tag,
      text: name,
      hint: el.getAttribute('aria-label') || el.getAttribute('placeholder') || '',
      enabled: !el.disabled,
      editable: el.isContentEditable || tag === 'textarea' || tag === 'input',
      checked: el.checked,
      inputType: el.type || '',
      visibility,
      bbox: [rect.x, rect.y, rect.width, rect.height],
      locator,
      occlusion: oc,
      fg,
      bg,
      landmark: landmarkOf(el),
      labelSource: labelSource(el, name),
      sources: ['VISIBLE_GEOMETRY','COMPUTED_STYLE','ROLE'],
      isModal,
      fontSize: parseFloat(style.fontSize || '16'),
      fontWeight: style.fontWeight || '400',
      isActive: document.activeElement === el,
    });
  };
  document.querySelectorAll('button, a, input, textarea, select, [role=\"button\"], [role=\"alert\"]').forEach((el) => {
    const tag = el.tagName.toLowerCase();
    let role = el.getAttribute('role') || tag;
    if (tag === 'input' && el.type === 'hidden') return;
    push(el, role, tag);
  });
  document.querySelectorAll('h1,h2,h3').forEach((el) => push(el, 'heading', el.tagName.toLowerCase()));
  return { elements: out.slice(0, 48), scroll, focusedIndex: null };
}
"""
