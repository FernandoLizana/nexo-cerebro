"""BrowserWorld — EnvironmentProtocol over a real browser (P2/P3)."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from nexo.core.action_schema import ActionSchema
from nexo_qa.browser.action_mapper import build_actions_from_scene, percept_triples_from_scene
from nexo_qa.browser.models import BrowserCommand, BrowserSnapshot
from nexo_qa.browser.playwright_driver import PlaywrightDriver
from nexo_qa.browser.policy import BrowserConfig, BrowserPolicy
from nexo_qa.perception import PerceptualAttentionGate, diff_scenes, perception_strategy_for
from nexo_qa.perception.models import PerceptualDiff, PerceptualScene


@dataclass
class BrowserWorld:
    """Translates web runtime ↔ NEXO environment contract."""

    initial_url: str
    config: BrowserConfig = field(default_factory=BrowserConfig)
    policy: BrowserPolicy | None = None
    driver: PlaywrightDriver | None = None
    seed: int = 42
    ticks: int = 0
    action_history: list[str] = field(default_factory=list)
    episodes: list[str] = field(default_factory=list)
    last_error: str | None = None
    goal: str = ""
    _snapshot: BrowserSnapshot | None = field(default=None, repr=False)
    _scene: PerceptualScene | None = field(default=None, repr=False)
    _previous_scene: PerceptualScene | None = field(default=None, repr=False)
    _last_diff: PerceptualDiff | None = field(default=None, repr=False)
    _scene_index: int = field(default=0, repr=False)
    _schemas: tuple[ActionSchema, ...] = field(default=(), repr=False)
    _commands: dict[str, BrowserCommand] = field(default_factory=dict, repr=False)
    _started: bool = field(default=False, repr=False)
    trace_log: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.policy is None:
            self.policy = BrowserPolicy(allowed_origins=self.config.allowed_origins)
        if self.driver is None:
            self.driver = PlaywrightDriver(config=self.config, policy=self.policy)

    @property
    def perceptual_scene(self) -> PerceptualScene | None:
        return self._scene

    @property
    def last_perceptual_diff(self) -> PerceptualDiff | None:
        return self._last_diff

    def start(self) -> None:
        assert self.driver is not None
        if not self._started:
            self.driver.start()
            try:
                if not self.policy.is_allowed_url(self.initial_url):
                    raise PermissionError(f"POLICY_BLOCKED: {self.initial_url}")
                self.driver.navigate(self.initial_url)
                self._refresh_catalog()
            except Exception:
                self.driver.close()
                raise
            self._started = True

    def reset(self) -> None:
        self.close()
        self.ticks = 0
        self.action_history.clear()
        self.last_error = None
        self.trace_log.clear()
        self._scene_index = 0
        self._previous_scene = None
        self.start()

    def close(self) -> None:
        if self.driver is not None:
            self.driver.close()
        self._started = False
        self._snapshot = None
        self._scene = None
        self._previous_scene = None
        self._last_diff = None
        self._schemas = ()
        self._commands.clear()

    def __enter__(self) -> BrowserWorld:
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def percepts_for_agent(self) -> list[tuple[str, float, tuple[float, ...]]]:
        self._ensure_started()
        assert self._scene is not None
        return percept_triples_from_scene(self._scene)

    def available_actions(self) -> tuple[str, ...]:
        self._ensure_started()
        return tuple(schema.id for schema in self._schemas)

    def action_info(self, action: str) -> dict[str, Any]:
        for schema in self._schemas:
            if schema.id == action:
                return {
                    "base_value": 0.35,
                    "cost_energy": float(schema.estimated_cost or 0.03),
                    "risk": float(schema.risk or 0.05),
                    "modality": str(schema.metadata.get("modality", "control")),
                }
        return {"base_value": 0.0, "cost_energy": 0.05, "risk": 0.1, "modality": ""}

    def action_schemas(self) -> tuple[ActionSchema, ...]:
        self._ensure_started()
        return self._schemas

    def action_salience_map(self) -> dict[str, float]:
        """Map action_id → salience from current perceptual scene."""
        self._ensure_started()
        if self._scene is None:
            return {}
        by_elem = {p.source_element_id: float(p.salience_score) for p in self._scene.percepts}
        result: dict[str, float] = {}
        for schema in self._schemas:
            sid = schema.metadata.get("source_element_id")
            if sid in by_elem:
                result[schema.id] = by_elem[sid]
        return result

    def apply_action(self, action: str) -> dict[str, Any]:
        self._ensure_started()
        self.ticks += 1
        if action not in self._commands:
            self.last_error = "ACTION_NO_LONGER_AVAILABLE"
            outcome = {
                "reward": 0.0,
                "homeostatic_deltas": {},
                "encoded_memory": None,
                "accepted": False,
                "success": False,
                "error": "ACTION_NO_LONGER_AVAILABLE",
            }
            self._trace("WEB_OUTCOME", {"action_id": action, **outcome})
            return outcome

        command = self._commands[action]
        assert self.driver is not None
        self._trace("BROWSER_COMMAND", command.to_dict())
        result = self.driver.execute(command)
        self._trace("BROWSER_RESULT", result.to_dict())

        url_before = self._snapshot.url if self._snapshot else ""
        self._refresh_catalog()
        url_after = self._snapshot.url if self._snapshot else result.url_after

        if result.failed:
            self.last_error = result.error_type
            outcome = {
                "reward": 0.0,
                "homeostatic_deltas": {},
                "encoded_memory": None,
                "accepted": False,
                "success": False,
                "error": result.error_type or "BROWSER_ERROR",
                "error_message": result.error_message,
            }
            self._trace("WEB_OUTCOME", {"action_id": action, **outcome})
            return outcome

        self.action_history.append(action)
        self.last_error = None
        reward = 0.15
        if result.navigation_occurred or result.url_changed:
            reward = 0.35
        if url_after.endswith("/success.html") or "success" in url_after:
            reward = 0.85
        outcome = {
            "reward": reward,
            "homeostatic_deltas": {"energy": -0.005},
            "encoded_memory": None,
            "accepted": True,
            "success": True,
            "error": None,
            "url_before": url_before,
            "url_after": url_after,
            "navigation": result.navigation_occurred,
        }
        self._trace("WEB_OUTCOME", {"action_id": action, **outcome})
        return outcome

    def sync_from_body(self, body: object) -> None:
        return None

    def _ensure_started(self) -> None:
        if not self._started:
            self.start()

    def _refresh_catalog(self) -> None:
        assert self.driver is not None
        mode = self.config.perception.mode
        self._snapshot = self.driver.snapshot(mode=mode)
        strategy = perception_strategy_for(self.config.perception)
        raw_scene = strategy.build_scene(self._snapshot, scene_index=self._scene_index)
        if mode.lower() == "dom_fast":
            scene = replace(
                raw_scene,
                attended_percept_ids=tuple(p.percept_id for p in raw_scene.percepts),
                focal_percept_ids=tuple(
                    p.percept_id for p in raw_scene.percepts[: self.config.perception.max_focal_percepts]
                ),
                peripheral_percept_ids=tuple(
                    p.percept_id
                    for p in raw_scene.percepts[
                        self.config.perception.max_focal_percepts : self.config.perception.max_attended_percepts
                    ]
                ),
            )
        else:
            scene = PerceptualAttentionGate(self.config.perception).apply(raw_scene)
        self._last_diff = diff_scenes(self._previous_scene, scene)
        self._previous_scene = scene
        self._scene = scene
        self._scene_index += 1
        self._schemas, self._commands = build_actions_from_scene(
            scene,
            self._snapshot,
            config=self.config.perception,
            test_data=self.config.test_data,
        )
        self._trace("BROWSER_SNAPSHOT", {"url": self._snapshot.url, "elements": len(self._snapshot.visible_elements)})
        self._trace("PERCEPTUAL_SCENE", scene.to_dict())
        if self._last_diff is not None:
            self._trace("PERCEPTUAL_DIFF", self._last_diff.to_dict())
        self._trace(
            "ATTENTION_TRACE",
            {
                "attended": list(scene.attended_percept_ids),
                "focal": list(scene.focal_percept_ids),
                "peripheral": list(scene.peripheral_percept_ids),
                "exclusion_audit": list(scene.exclusion_audit),
            },
        )
        self._trace(
            "WEB_ACTIONS_AVAILABLE",
            {"candidate_action_ids": [s.id for s in self._schemas], "labels": [s.label for s in self._schemas]},
        )

    def _trace(self, event_type: str, payload: dict[str, Any]) -> None:
        self.trace_log.append({"tick": self.ticks, "event_type": event_type, "payload": payload})
