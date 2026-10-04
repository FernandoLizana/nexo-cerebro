"""Snapshot / scene → ActionSchema and action_id → BrowserCommand (internal only)."""

from __future__ import annotations

from nexo.core.action_schema import ActionSchema
from nexo_qa.browser.models import BrowserCommand, BrowserElementSnapshot, BrowserSnapshot
from nexo_qa.perception.config import PerceptionConfig
from nexo_qa.perception.models import PerceptualScene, WebPercept


def _region_from_bbox(box: tuple[float, float, float, float] | None, viewport: tuple[int, int]) -> str:
    if not box:
        return "center"
    _x, y, _w, h = box
    vw, vh = viewport
    cy = y + h / 2
    cx = _x + _w / 2
    vert = "upper" if cy < vh * 0.33 else "lower" if cy > vh * 0.66 else "middle"
    horiz = "left" if cx < vw * 0.33 else "right" if cx > vw * 0.66 else "center"
    if vert == "middle" and horiz == "center":
        return "center"
    return f"{vert}-{horiz}"


def _label_for_element(element: BrowserElementSnapshot) -> str:
    text = (element.visible_text or element.semantic_hint or element.role or element.tag).strip()
    return text[:80] if text else element.element_id


def percept_action_eligible(percept: WebPercept, config: PerceptionConfig) -> bool:
    if not percept.interactive:
        return False
    if not percept.enabled:
        return False
    if percept.viewport_relation.startswith("OFFSCREEN"):
        return False
    if percept.viewport_relation == "OCCLUDED":
        return False
    if percept.visibility_score < config.min_visibility_for_action:
        return False
    if percept.occlusion_score >= config.occlusion_threshold:
        return False
    return True


def _element_for_percept(snapshot: BrowserSnapshot, percept: WebPercept) -> BrowserElementSnapshot | None:
    for element in snapshot.visible_elements:
        if element.element_id == percept.source_element_id:
            return element
    return None


def build_actions_from_scene(
    scene: PerceptualScene,
    snapshot: BrowserSnapshot,
    *,
    config: PerceptionConfig | None = None,
    test_data: dict[str, str] | None = None,
) -> tuple[tuple[ActionSchema, ...], dict[str, BrowserCommand]]:
    """Build cognitive actions from perceptual scene (P3)."""
    config = config or PerceptionConfig()
    test_data = test_data or {}
    hybrid = config.mode.lower() == "hybrid"
    schemas: list[ActionSchema] = []
    commands: dict[str, BrowserCommand] = {}
    seq = 0

    def add_action(
        *,
        prefix: str,
        label: str,
        action_type: str,
        affordance: str,
        effect: str,
        command: BrowserCommand,
        cost: float = 0.03,
        risk: float = 0.05,
        modality: str = "control",
        source_percept_id: str | None = None,
        source_element_id: str | None = None,
    ) -> None:
        nonlocal seq
        seq += 1
        action_id = f"web:{prefix}:{seq:04d}"
        metadata = {
            "source": "browser_world",
            "modality": modality,
            "role": command.command_type.lower(),
        }
        if source_percept_id:
            metadata["source_percept_id"] = source_percept_id
        if source_element_id:
            metadata["source_element_id"] = source_element_id
        schemas.append(
            ActionSchema(
                id=action_id,
                label=label,
                action_type=action_type,
                target=label,
                affordance=affordance,
                expected_effect=effect,
                estimated_cost=cost,
                risk=risk,
                metadata=metadata,
            )
        )
        commands[action_id] = command

    for percept in scene.percepts:
        if not percept_action_eligible(percept, config):
            continue
        if hybrid and percept.attention_tier == "UNATTENDED":
            continue
        element = _element_for_percept(snapshot, percept)
        if element is None:
            continue
        label = percept.label or _label_for_element(element)

        if element.role in ("button", "link") or element.tag in ("button", "a"):
            add_action(
                prefix="activate",
                label=f'activate "{label}"',
                action_type="activate",
                affordance="selectable",
                effect="navigate_or_submit",
                command=BrowserCommand(command_type="CLICK", element_id=element.element_id),
                modality=element.role or "button",
                source_percept_id=percept.percept_id,
                source_element_id=element.element_id,
            )
            continue

        if element.editable or element.tag in ("input", "textarea"):
            add_action(
                prefix="focus",
                label=f'focus "{label}"',
                action_type="focus",
                affordance="selectable",
                effect="prepare_input",
                command=BrowserCommand(command_type="FOCUS", element_id=element.element_id),
                cost=0.02,
                risk=0.02,
                modality="input",
                source_percept_id=percept.percept_id,
                source_element_id=element.element_id,
            )
            text_value = test_data.get("name") or test_data.get("email") or test_data.get("text") or "Nexo Test"
            if element.input_type not in ("checkbox", "radio", "hidden"):
                add_action(
                    prefix="type",
                    label=f'type into "{label}"',
                    action_type="type",
                    affordance="selectable",
                    effect="fill_field",
                    command=BrowserCommand(
                        command_type="TYPE",
                        element_id=element.element_id,
                        text=text_value,
                    ),
                    cost=0.04,
                    risk=0.03,
                    modality="input",
                    source_percept_id=percept.percept_id,
                    source_element_id=element.element_id,
                )
            if element.input_type == "checkbox":
                add_action(
                    prefix="toggle",
                    label=f'toggle "{label}"',
                    action_type="toggle",
                    affordance="selectable",
                    effect="toggle",
                    command=BrowserCommand(command_type="TOGGLE", element_id=element.element_id),
                    modality="checkbox",
                    source_percept_id=percept.percept_id,
                    source_element_id=element.element_id,
                )

    add_action(
        prefix="scroll",
        label="scroll down",
        action_type="scroll",
        affordance="navigable",
        effect="reveal",
        command=BrowserCommand(command_type="SCROLL", scroll_direction="down"),
        cost=0.01,
        risk=0.0,
        modality="viewport",
    )
    add_action(
        prefix="navigate",
        label="go back",
        action_type="navigate",
        affordance="navigable",
        effect="return",
        command=BrowserCommand(command_type="BACK"),
        cost=0.02,
        risk=0.05,
        modality="navigation",
    )

    return tuple(schemas), commands


def build_actions_from_snapshot(
    snapshot: BrowserSnapshot,
    *,
    test_data: dict[str, str] | None = None,
    config: PerceptionConfig | None = None,
) -> tuple[tuple[ActionSchema, ...], dict[str, BrowserCommand]]:
    """Legacy P2 entry — routes through dom_fast scene when config provided."""
    from nexo_qa.perception.dom_fast import DomFastPerception

    perception = config or PerceptionConfig(mode="dom_fast")
    scene = DomFastPerception(perception).build_scene(snapshot)
    return build_actions_from_scene(scene, snapshot, config=perception, test_data=test_data)


def percept_triples_from_scene(scene: PerceptualScene) -> list[tuple[str, float, tuple[float, ...]]]:
    """Generic P1 percept tuples from attended perceptual scene."""
    percepts: list[tuple[str, float, tuple[float, ...]]] = []
    attended = [p for p in scene.percepts if p.attention_tier in ("FOCAL", "PERIPHERAL")]
    if not attended:
        attended = list(scene.percepts[:12])
    for percept in attended[:12]:
        modality = percept.role or percept.kind or "control"
        salience = min(1.0, percept.salience_score)
        label_hash = hash(percept.label) % 1000 / 1000.0
        percepts.append(
            (
                modality,
                salience,
                (label_hash, percept.visibility_score, hash(percept.visual_region) % 100 / 100.0),
            )
        )
    title = scene.global_context.get("title") or ""
    if title:
        percepts.append(("heading", 0.4, (hash(title) % 1000 / 1000.0, 0.0, 0.0)))
    return percepts


def percept_triples_from_snapshot(snapshot: BrowserSnapshot) -> list[tuple[str, float, tuple[float, ...]]]:
    """Generic P1 percept tuples from DOM_FAST snapshot."""
    from nexo_qa.perception.dom_fast import DomFastPerception

    scene = DomFastPerception(PerceptionConfig(mode="dom_fast")).build_scene(snapshot)
    return percept_triples_from_scene(scene)
