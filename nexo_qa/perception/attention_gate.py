"""Limit percepts reaching cognition — focal vs peripheral vs unattended."""

from __future__ import annotations

from dataclasses import replace

from nexo_qa.perception.config import PerceptionConfig
from nexo_qa.perception.models import PerceptualScene, WebPercept


class PerceptualAttentionGate:
    """Deterministic attention budget before NEXO cognition."""

    def __init__(self, config: PerceptionConfig) -> None:
        self.config = config

    def apply(self, scene: PerceptualScene) -> PerceptualScene:
        eligible = [
            p
            for p in scene.percepts
            if p.visibility_score > 0.05
            and p.viewport_relation not in ("OFFSCREEN_ABOVE", "OFFSCREEN_BELOW", "OFFSCREEN_LEFT", "OFFSCREEN_RIGHT")
        ]
        ranked = sorted(
            eligible,
            key=lambda p: (p.salience_score * p.visibility_score * (1.0 - p.occlusion_score), p.percept_id),
            reverse=True,
        )
        attended = ranked[: self.config.max_attended_percepts]
        focal_ids = {p.percept_id for p in attended[: self.config.max_focal_percepts]}
        peripheral_ids = {p.percept_id for p in attended[self.config.max_focal_percepts :]}
        updated: list[WebPercept] = []
        audit = list(scene.exclusion_audit)
        for percept in scene.percepts:
            if percept.percept_id in focal_ids:
                updated.append(replace(percept, attention_tier="FOCAL"))
            elif percept.percept_id in peripheral_ids:
                updated.append(replace(percept, attention_tier="PERIPHERAL"))
            else:
                if percept.visibility_score > 0 and percept.percept_id not in focal_ids | peripheral_ids:
                    audit.append(
                        {
                            "source_element_id": percept.source_element_id,
                            "percept_id": percept.percept_id,
                            "reason": "ATTENTION_LIMIT",
                        }
                    )
                updated.append(replace(percept, attention_tier="UNATTENDED"))
        return replace(
            scene,
            percepts=tuple(updated),
            attended_percept_ids=tuple(p.percept_id for p in attended),
            focal_percept_ids=tuple(p for p in focal_ids),
            peripheral_percept_ids=tuple(p for p in peripheral_ids),
            exclusion_audit=tuple(audit),
        )
