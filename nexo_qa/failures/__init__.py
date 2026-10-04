"""Cognitive failure taxonomy and certificates."""

from nexo_qa.failures.certificate import (
    CognitiveFailureCertificate,
    build_certificate,
    validate_certificate,
)
from nexo_qa.failures.classifier import ClassifierResult, FailureClassifier
from nexo_qa.failures.episodes import FailureEpisode, merge_failures_into_episodes
from nexo_qa.failures.severity import compute_severity
from nexo_qa.failures.taxonomy import (
    CLASSIFICATION_VERSION,
    CognitiveFailure,
    CognitiveFailureType,
    FailureFamily,
)

__all__ = [
    "CLASSIFICATION_VERSION",
    "ClassifierResult",
    "CognitiveFailure",
    "CognitiveFailureCertificate",
    "CognitiveFailureType",
    "FailureClassifier",
    "FailureEpisode",
    "FailureFamily",
    "build_certificate",
    "compute_severity",
    "merge_failures_into_episodes",
    "validate_certificate",
]
