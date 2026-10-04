"""Rule-based failure classifier — deterministic, offline, no expected-step path."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nexo_qa.analysis.models import CognitiveQAEvent, CognitiveQAObservation, RawRunTrace, _new_id
from nexo_qa.failures.severity import compute_severity
from nexo_qa.failures.taxonomy import (
    CLASSIFICATION_VERSION,
    CognitiveFailure,
    CognitiveFailureType,
    FAILURE_FAMILY_MAP,
    FailureFamily,
)


@dataclass
class ClassifierResult:
    observations: list[CognitiveQAObservation]
    failures: list[CognitiveFailure]
    classification_version: str = CLASSIFICATION_VERSION


class FailureClassifier:
    """Rule-based classifier over normalized events — no oracle golden path."""

    def classify(
        self,
        events: list[CognitiveQAEvent],
        raw: RawRunTrace,
    ) -> ClassifierResult:
        observations: list[CognitiveQAObservation] = []
        failures: list[CognitiveFailure] = []
        meta = raw.metadata
        goal_id = meta.get("goal_id")
        persona_id = meta.get("persona_id")
        action_history = list(meta.get("action_history") or [])
        goal_rel = dict(meta.get("goal_relevance") or {})
        salience = dict(meta.get("action_salience") or {})

        # --- Observations: repeated actions ---
        if len(action_history) >= 3:
            last3 = action_history[-3:]
            if len(set(last3)) == 1:
                obs_id = _new_id("obs")
                observations.append(
                    CognitiveQAObservation(
                        observation_id=obs_id,
                        category="BEHAVIOR",
                        description=f"Repeated same action {last3[0]} three times",
                        start_tick=max(0, raw.ticks - 3),
                        end_tick=raw.ticks,
                        severity_hint="LOW",
                        confidence=0.9,
                        evidence_refs=(obs_id,),
                    )
                )

        # --- Failures from NEXO events ---
        for ev in events:
            et = ev.event_type
            if et == "goal.drift":
                failures.append(self._make_failure(
                    CognitiveFailureType.GOAL_DRIFT, ev, goal_id, persona_id,
                    goal_impact=0.5, persistence=0.4, role="contributor",
                ))
            elif et == "goal.behavior_loop":
                failures.append(self._make_failure(
                    CognitiveFailureType.NAVIGATION_LOOP, ev, goal_id, persona_id,
                    goal_impact=0.55, persistence=0.6,
                ))
            elif et == "goal.progress":
                level = (ev.evidence.get("payload") or {}).get("progress", {}).get("level")
                if level == "none" and ev.tick >= 5:
                    failures.append(self._make_failure(
                        CognitiveFailureType.NO_PROGRESS, ev, goal_id, persona_id,
                        goal_impact=0.45, persistence=0.5,
                    ))
                elif level == "blocked":
                    failures.append(self._make_failure(
                        CognitiveFailureType.BLOCKED_GOAL, ev, goal_id, persona_id,
                        goal_impact=0.7, terminal_failure=True, role="terminal",
                    ))

        # --- Policy / interaction from world outcomes ---
        for wt in raw.world_trace:
            if wt.get("event_type") != "WEB_OUTCOME":
                continue
            payload = wt.get("payload") or {}
            err = payload.get("error") or payload.get("error_message")
            tick = int(wt.get("tick", 0))
            if err == "POLICY_BLOCKED":
                fake_ev = CognitiveQAEvent(
                    event_id=_new_id("qaev"), trace_id=_new_id("tr"), run_id=raw.run_id,
                    tick=tick, simulation_time=float(tick), event_type="policy.blocked",
                    source="browser_world", goal_id=goal_id, persona_id=persona_id,
                    evidence={"payload": payload},
                )
                failures.append(self._make_failure(
                    CognitiveFailureType.ACTION_POLICY_BLOCKED, fake_ev, goal_id, persona_id,
                    goal_impact=0.6, risk_weight=0.3, role="terminal",
                ))
            elif err == "ACTION_NO_LONGER_AVAILABLE":
                fake_ev = CognitiveQAEvent(
                    event_id=_new_id("qaev"), trace_id=_new_id("tr"), run_id=raw.run_id,
                    tick=tick, simulation_time=float(tick), event_type="interaction.unavailable",
                    source="browser_world", goal_id=goal_id, persona_id=persona_id,
                    evidence={"payload": payload},
                )
                failures.append(self._make_failure(
                    CognitiveFailureType.ACTION_NO_LONGER_AVAILABLE, fake_ev, goal_id, persona_id,
                    goal_impact=0.35,
                ))

        # --- Distractor capture heuristic ---
        if action_history and goal_rel and salience:
            last_action = action_history[-1]
            rel = float(goal_rel.get(last_action, 0.0))
            sal = float(salience.get(last_action, 0.0))
            if sal > 0.55 and rel < 0.35:
                fake_ev = CognitiveQAEvent(
                    event_id=_new_id("qaev"), trace_id=_new_id("tr"), run_id=raw.run_id,
                    tick=raw.ticks, simulation_time=float(raw.ticks),
                    event_type="attention.distractor_capture", source="classifier",
                    goal_id=goal_id, persona_id=persona_id, action_id=last_action,
                    evidence={"salience": sal, "goal_relevance": rel},
                )
                failures.append(self._make_failure(
                    CognitiveFailureType.DISTRACTOR_CAPTURE, fake_ev, goal_id, persona_id,
                    goal_impact=0.5, persistence=0.35, role="contributor",
                ))

        # --- Attention: goal-relevant visible but not attended ---
        for ev in events:
            if ev.event_type != "world.attention_trace":
                continue
            payload = ev.evidence.get("payload") or {}
            attended = set(payload.get("attended") or [])
            labels = payload.get("labels") or []
            for label in labels:
                if not label or not isinstance(label, str):
                    continue
                label_lower = label.lower()
                if any(tok in label_lower for tok in ("continue", "basic", "pro", "plan")):
                    if attended and label not in attended and str(label) not in attended:
                        failures.append(self._make_failure(
                            CognitiveFailureType.TARGET_VISIBLE_NOT_ATTENDED, ev, goal_id, persona_id,
                            goal_impact=0.4, confidence=0.65,
                        ))
                        break

        # --- Frustration from persona.state events ---
        frust_values: list[float] = []
        for ev in events:
            if ev.event_type == "persona.state":
                st = (ev.evidence.get("payload") or {}).get("state") or {}
                frust_values.append(float(st.get("current_frustration", 0.0)))
            elif ev.event_type == "affect.updated":
                frust_values.append(float((ev.evidence.get("payload") or {}).get("frustration", 0.0)))
        if len(frust_values) >= 2 and frust_values[-1] - frust_values[0] > 0.15:
            fake_ev = CognitiveQAEvent(
                event_id=_new_id("qaev"), trace_id=_new_id("tr"), run_id=raw.run_id,
                tick=raw.ticks, simulation_time=float(raw.ticks),
                event_type="frustration.spike", source="classifier",
                goal_id=goal_id, persona_id=persona_id,
                evidence={"frustration_delta": frust_values[-1] - frust_values[0]},
            )
            failures.append(self._make_failure(
                CognitiveFailureType.FRUSTRATION_SPIKE, fake_ev, goal_id, persona_id,
                goal_impact=0.3, confidence=0.7, role="associated_with",
            ))

        # --- WM loss from working_memory events ---
        wm_counts: list[int] = []
        for ev in events:
            if ev.event_type == "working_memory.updated":
                items = (ev.evidence.get("payload") or {}).get("items") or []
                wm_counts.append(len(items))
        if wm_counts and max(wm_counts) == 0 and raw.ticks > 8:
            fake_ev = CognitiveQAEvent(
                event_id=_new_id("qaev"), trace_id=_new_id("tr"), run_id=raw.run_id,
                tick=raw.ticks, simulation_time=float(raw.ticks),
                event_type="memory.wm_empty", source="classifier",
                goal_id=goal_id, persona_id=persona_id,
            )
            failures.append(self._make_failure(
                CognitiveFailureType.WORKING_MEMORY_LOSS, fake_ev, goal_id, persona_id,
                goal_impact=0.35, confidence=0.55,
            ))

        # --- Deliberation conflict ---
        for ev in events:
            if ev.event_type != "deliberation.completed":
                continue
            payload = ev.evidence.get("payload") or {}
            conflict = float(payload.get("conflict", 0.0))
            if conflict > 0.35:
                failures.append(self._make_failure(
                    CognitiveFailureType.HIGH_UNCERTAINTY_CHOICE, ev, goal_id, persona_id,
                    goal_impact=0.25, confidence=min(0.95, 0.5 + conflict),
                ))

        # --- Recovery detection: failure then progress improvement ---
        progress_levels: list[str] = []
        for ev in events:
            if ev.event_type == "goal.progress":
                pl = (ev.evidence.get("payload") or {}).get("progress", {}).get("level", "none")
                progress_levels.append(str(pl))
        if len(progress_levels) >= 2 and progress_levels[0] in ("none", "partial") and progress_levels[-1] in ("high", "complete"):
            for f in failures:
                if f.failure_type in (CognitiveFailureType.NO_PROGRESS, CognitiveFailureType.GOAL_DRIFT):
                    f = self._mark_recovered(f)
            failures = [self._mark_recovered(f) if f.failure_type in (
                CognitiveFailureType.NO_PROGRESS, CognitiveFailureType.GOAL_DRIFT, CognitiveFailureType.NAVIGATION_LOOP,
            ) else f for f in failures]

        return ClassifierResult(observations=observations, failures=failures)

    def _make_failure(
        self,
        ftype: CognitiveFailureType,
        ev: CognitiveQAEvent,
        goal_id: str | None,
        persona_id: str | None,
        *,
        goal_impact: float = 0.3,
        recovery_cost: float = 0.0,
        risk_weight: float = 0.0,
        persistence: float = 0.0,
        terminal_failure: bool = False,
        confidence: float = 0.75,
        role: str = "symptom",
        recovered: bool = False,
    ) -> CognitiveFailure:
        sev = compute_severity(
            goal_impact=goal_impact,
            recovery_cost=recovery_cost,
            risk_weight=risk_weight,
            persistence=persistence,
            terminal_failure=terminal_failure,
        )
        family = FAILURE_FAMILY_MAP.get(ftype, FailureFamily.UNKNOWN)
        return CognitiveFailure(
            failure_id=_new_id("fail"),
            failure_type=ftype,
            family=family,
            severity=sev.severity,
            confidence=confidence,
            start_tick=ev.tick,
            end_tick=ev.tick,
            goal_id=goal_id,
            persona_id=persona_id,
            primary_evidence=(ev.event_id,),
            supporting_evidence=(),
            causal_links=({"relation": "associated_with", "event_id": ev.event_id},),
            recoverable=not terminal_failure,
            recovered=recovered,
            impact="goal_progress" if goal_impact > 0.4 else "minor",
            role=role,
        )

    def _mark_recovered(self, f: CognitiveFailure) -> CognitiveFailure:
        from dataclasses import replace
        return replace(f, recovered=True, role="symptom")
