"""Versioned cognitive failure taxonomy — P6."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

CLASSIFICATION_VERSION = "failures-v1"


class FailureFamily(str, Enum):
    PERCEPTION = "PERCEPTION"
    ATTENTION = "ATTENTION"
    SEMANTIC = "SEMANTIC"
    MEMORY = "MEMORY"
    DECISION = "DECISION"
    NAVIGATION = "NAVIGATION"
    RECOVERY = "RECOVERY"
    FRUSTRATION = "FRUSTRATION"
    FATIGUE = "FATIGUE"
    RISK = "RISK"
    PROGRESS = "PROGRESS"
    INTERACTION = "INTERACTION"
    SYSTEM_FEEDBACK = "SYSTEM_FEEDBACK"
    POLICY = "POLICY"
    UNKNOWN = "UNKNOWN"


class CognitiveFailureType(str, Enum):
    # Perception
    TARGET_NOT_VISIBLE = "TARGET_NOT_VISIBLE"
    TARGET_OFFSCREEN = "TARGET_OFFSCREEN"
    TARGET_OCCLUDED = "TARGET_OCCLUDED"
    LOW_STRUCTURAL_VISIBILITY = "LOW_STRUCTURAL_VISIBILITY"
    PERCEPT_NOT_GENERATED = "PERCEPT_NOT_GENERATED"
    PERCEPTUAL_MISS = "PERCEPTUAL_MISS"
    # Attention
    TARGET_VISIBLE_NOT_ATTENDED = "TARGET_VISIBLE_NOT_ATTENDED"
    DISTRACTOR_CAPTURE = "DISTRACTOR_CAPTURE"
    ATTENTION_SWITCH = "ATTENTION_SWITCH"
    ATTENTION_DECAY = "ATTENTION_DECAY"
    ATTENTION_OVERLOAD = "ATTENTION_OVERLOAD"
    # Semantic
    AMBIGUOUS_LABEL = "AMBIGUOUS_LABEL"
    MISINTERPRETED_AFFORDANCE = "MISINTERPRETED_AFFORDANCE"
    LOW_GOAL_RELEVANCE_MATCH = "LOW_GOAL_RELEVANCE_MATCH"
    DUPLICATE_LABEL_CONFUSION = "DUPLICATE_LABEL_CONFUSION"
    SEMANTIC_UNCERTAINTY = "SEMANTIC_UNCERTAINTY"
    # Memory
    WORKING_MEMORY_LOSS = "WORKING_MEMORY_LOSS"
    FAILED_RETRIEVAL = "FAILED_RETRIEVAL"
    STALE_MEMORY = "STALE_MEMORY"
    CONFLICTING_MEMORY = "CONFLICTING_MEMORY"
    FORGOTTEN_CONTEXT = "FORGOTTEN_CONTEXT"
    # Decision
    SUBOPTIMAL_CHOICE = "SUBOPTIMAL_CHOICE"
    HIGH_UNCERTAINTY_CHOICE = "HIGH_UNCERTAINTY_CHOICE"
    IMPULSIVE_CHOICE = "IMPULSIVE_CHOICE"
    RISKY_CHOICE = "RISKY_CHOICE"
    LOW_EXPECTED_PROGRESS_CHOICE = "LOW_EXPECTED_PROGRESS_CHOICE"
    # Navigation
    DEAD_END = "DEAD_END"
    BACKTRACK = "BACKTRACK"
    NAVIGATION_LOOP = "NAVIGATION_LOOP"
    UNPRODUCTIVE_SCROLL = "UNPRODUCTIVE_SCROLL"
    WRONG_SECTION = "WRONG_SECTION"
    STATE_REVISIT_LOOP = "STATE_REVISIT_LOOP"
    # Recovery
    FAILED_TO_RECOVER = "FAILED_TO_RECOVER"
    REPEATED_SAME_ERROR = "REPEATED_SAME_ERROR"
    RECOVERY_LOOP = "RECOVERY_LOOP"
    NO_ALTERNATIVE_FOUND = "NO_ALTERNATIVE_FOUND"
    RECOVERY_TOO_COSTLY = "RECOVERY_TOO_COSTLY"
    # Frustration
    FRUSTRATION_SPIKE = "FRUSTRATION_SPIKE"
    FRUSTRATION_ACCUMULATION = "FRUSTRATION_ACCUMULATION"
    FRUSTRATION_ASSOCIATED_ABANDONMENT = "FRUSTRATION_ASSOCIATED_ABANDONMENT"
    # Fatigue
    FATIGUE_ACCUMULATION = "FATIGUE_ACCUMULATION"
    FATIGUE_ATTENTION_DEGRADATION = "FATIGUE_ATTENTION_DEGRADATION"
    FATIGUE_DECISION_DEGRADATION = "FATIGUE_DECISION_DEGRADATION"
    # Risk
    UNSAFE_ACTION = "UNSAFE_ACTION"
    IGNORED_WARNING = "IGNORED_WARNING"
    HIGH_RISK_LOW_CONFIDENCE_ACTION = "HIGH_RISK_LOW_CONFIDENCE_ACTION"
    IRREVERSIBLE_ACTION_UNDER_UNCERTAINTY = "IRREVERSIBLE_ACTION_UNDER_UNCERTAINTY"
    # Progress
    NO_PROGRESS = "NO_PROGRESS"
    PROGRESS_REGRESSION = "PROGRESS_REGRESSION"
    STAGNATION = "STAGNATION"
    GOAL_DRIFT = "GOAL_DRIFT"
    BLOCKED_GOAL = "BLOCKED_GOAL"
    # Interaction
    DISABLED_CONTROL = "DISABLED_CONTROL"
    ACTION_NO_LONGER_AVAILABLE = "ACTION_NO_LONGER_AVAILABLE"
    FORM_VALIDATION_FAILURE = "FORM_VALIDATION_FAILURE"
    INPUT_MISMATCH = "INPUT_MISMATCH"
    MISCLICK_EQUIVALENT = "MISCLICK_EQUIVALENT"
    # System feedback
    ERROR_NOT_SALIENT = "ERROR_NOT_SALIENT"
    FEEDBACK_DELAYED = "FEEDBACK_DELAYED"
    FEEDBACK_AMBIGUOUS = "FEEDBACK_AMBIGUOUS"
    STATE_CHANGE_NOT_OBVIOUS = "STATE_CHANGE_NOT_OBVIOUS"
    CONFIRMATION_UNCLEAR = "CONFIRMATION_UNCLEAR"
    # Policy
    NAVIGATION_BLOCKED = "NAVIGATION_BLOCKED"
    ACTION_POLICY_BLOCKED = "ACTION_POLICY_BLOCKED"
    SECURITY_POLICY_TRIGGERED = "SECURITY_POLICY_TRIGGERED"
    # Unknown
    UNCLASSIFIED_FAILURE = "UNCLASSIFIED_FAILURE"


FAILURE_FAMILY_MAP: dict[CognitiveFailureType, FailureFamily] = {
    CognitiveFailureType.TARGET_NOT_VISIBLE: FailureFamily.PERCEPTION,
    CognitiveFailureType.TARGET_OFFSCREEN: FailureFamily.PERCEPTION,
    CognitiveFailureType.TARGET_OCCLUDED: FailureFamily.PERCEPTION,
    CognitiveFailureType.LOW_STRUCTURAL_VISIBILITY: FailureFamily.PERCEPTION,
    CognitiveFailureType.PERCEPT_NOT_GENERATED: FailureFamily.PERCEPTION,
    CognitiveFailureType.PERCEPTUAL_MISS: FailureFamily.PERCEPTION,
    CognitiveFailureType.TARGET_VISIBLE_NOT_ATTENDED: FailureFamily.ATTENTION,
    CognitiveFailureType.DISTRACTOR_CAPTURE: FailureFamily.ATTENTION,
    CognitiveFailureType.ATTENTION_SWITCH: FailureFamily.ATTENTION,
    CognitiveFailureType.ATTENTION_DECAY: FailureFamily.ATTENTION,
    CognitiveFailureType.ATTENTION_OVERLOAD: FailureFamily.ATTENTION,
    CognitiveFailureType.AMBIGUOUS_LABEL: FailureFamily.SEMANTIC,
    CognitiveFailureType.MISINTERPRETED_AFFORDANCE: FailureFamily.SEMANTIC,
    CognitiveFailureType.LOW_GOAL_RELEVANCE_MATCH: FailureFamily.SEMANTIC,
    CognitiveFailureType.DUPLICATE_LABEL_CONFUSION: FailureFamily.SEMANTIC,
    CognitiveFailureType.SEMANTIC_UNCERTAINTY: FailureFamily.SEMANTIC,
    CognitiveFailureType.WORKING_MEMORY_LOSS: FailureFamily.MEMORY,
    CognitiveFailureType.FAILED_RETRIEVAL: FailureFamily.MEMORY,
    CognitiveFailureType.STALE_MEMORY: FailureFamily.MEMORY,
    CognitiveFailureType.CONFLICTING_MEMORY: FailureFamily.MEMORY,
    CognitiveFailureType.FORGOTTEN_CONTEXT: FailureFamily.MEMORY,
    CognitiveFailureType.SUBOPTIMAL_CHOICE: FailureFamily.DECISION,
    CognitiveFailureType.HIGH_UNCERTAINTY_CHOICE: FailureFamily.DECISION,
    CognitiveFailureType.IMPULSIVE_CHOICE: FailureFamily.DECISION,
    CognitiveFailureType.RISKY_CHOICE: FailureFamily.RISK,
    CognitiveFailureType.LOW_EXPECTED_PROGRESS_CHOICE: FailureFamily.DECISION,
    CognitiveFailureType.DEAD_END: FailureFamily.NAVIGATION,
    CognitiveFailureType.BACKTRACK: FailureFamily.NAVIGATION,
    CognitiveFailureType.NAVIGATION_LOOP: FailureFamily.NAVIGATION,
    CognitiveFailureType.UNPRODUCTIVE_SCROLL: FailureFamily.NAVIGATION,
    CognitiveFailureType.WRONG_SECTION: FailureFamily.NAVIGATION,
    CognitiveFailureType.STATE_REVISIT_LOOP: FailureFamily.NAVIGATION,
    CognitiveFailureType.FAILED_TO_RECOVER: FailureFamily.RECOVERY,
    CognitiveFailureType.REPEATED_SAME_ERROR: FailureFamily.RECOVERY,
    CognitiveFailureType.RECOVERY_LOOP: FailureFamily.RECOVERY,
    CognitiveFailureType.NO_ALTERNATIVE_FOUND: FailureFamily.RECOVERY,
    CognitiveFailureType.RECOVERY_TOO_COSTLY: FailureFamily.RECOVERY,
    CognitiveFailureType.FRUSTRATION_SPIKE: FailureFamily.FRUSTRATION,
    CognitiveFailureType.FRUSTRATION_ACCUMULATION: FailureFamily.FRUSTRATION,
    CognitiveFailureType.FRUSTRATION_ASSOCIATED_ABANDONMENT: FailureFamily.FRUSTRATION,
    CognitiveFailureType.FATIGUE_ACCUMULATION: FailureFamily.FATIGUE,
    CognitiveFailureType.FATIGUE_ATTENTION_DEGRADATION: FailureFamily.FATIGUE,
    CognitiveFailureType.FATIGUE_DECISION_DEGRADATION: FailureFamily.FATIGUE,
    CognitiveFailureType.UNSAFE_ACTION: FailureFamily.RISK,
    CognitiveFailureType.IGNORED_WARNING: FailureFamily.RISK,
    CognitiveFailureType.HIGH_RISK_LOW_CONFIDENCE_ACTION: FailureFamily.RISK,
    CognitiveFailureType.IRREVERSIBLE_ACTION_UNDER_UNCERTAINTY: FailureFamily.RISK,
    CognitiveFailureType.NO_PROGRESS: FailureFamily.PROGRESS,
    CognitiveFailureType.PROGRESS_REGRESSION: FailureFamily.PROGRESS,
    CognitiveFailureType.STAGNATION: FailureFamily.PROGRESS,
    CognitiveFailureType.GOAL_DRIFT: FailureFamily.PROGRESS,
    CognitiveFailureType.BLOCKED_GOAL: FailureFamily.PROGRESS,
    CognitiveFailureType.DISABLED_CONTROL: FailureFamily.INTERACTION,
    CognitiveFailureType.ACTION_NO_LONGER_AVAILABLE: FailureFamily.INTERACTION,
    CognitiveFailureType.FORM_VALIDATION_FAILURE: FailureFamily.INTERACTION,
    CognitiveFailureType.INPUT_MISMATCH: FailureFamily.INTERACTION,
    CognitiveFailureType.MISCLICK_EQUIVALENT: FailureFamily.INTERACTION,
    CognitiveFailureType.ERROR_NOT_SALIENT: FailureFamily.SYSTEM_FEEDBACK,
    CognitiveFailureType.FEEDBACK_DELAYED: FailureFamily.SYSTEM_FEEDBACK,
    CognitiveFailureType.FEEDBACK_AMBIGUOUS: FailureFamily.SYSTEM_FEEDBACK,
    CognitiveFailureType.STATE_CHANGE_NOT_OBVIOUS: FailureFamily.SYSTEM_FEEDBACK,
    CognitiveFailureType.CONFIRMATION_UNCLEAR: FailureFamily.SYSTEM_FEEDBACK,
    CognitiveFailureType.NAVIGATION_BLOCKED: FailureFamily.POLICY,
    CognitiveFailureType.ACTION_POLICY_BLOCKED: FailureFamily.POLICY,
    CognitiveFailureType.SECURITY_POLICY_TRIGGERED: FailureFamily.POLICY,
    CognitiveFailureType.UNCLASSIFIED_FAILURE: FailureFamily.UNKNOWN,
}


@dataclass(frozen=True, slots=True)
class CognitiveFailure:
    failure_id: str
    failure_type: CognitiveFailureType
    family: FailureFamily
    severity: str
    confidence: float
    start_tick: int
    end_tick: int
    goal_id: str | None
    persona_id: str | None
    primary_evidence: tuple[str, ...]
    supporting_evidence: tuple[str, ...] = ()
    causal_links: tuple[dict[str, str], ...] = ()
    recoverable: bool = True
    recovered: bool = False
    impact: str = "unknown"
    classification_version: str = CLASSIFICATION_VERSION
    role: str = "symptom"  # contributor | symptom | terminal

    def to_dict(self) -> dict:
        return {
            "failure_id": self.failure_id,
            "failure_type": self.failure_type.value,
            "family": self.family.value,
            "severity": self.severity,
            "confidence": round(self.confidence, 4),
            "start_tick": self.start_tick,
            "end_tick": self.end_tick,
            "goal_id": self.goal_id,
            "persona_id": self.persona_id,
            "primary_evidence": list(self.primary_evidence),
            "supporting_evidence": list(self.supporting_evidence),
            "causal_links": list(self.causal_links),
            "recoverable": self.recoverable,
            "recovered": self.recovered,
            "impact": self.impact,
            "classification_version": self.classification_version,
            "role": self.role,
        }
