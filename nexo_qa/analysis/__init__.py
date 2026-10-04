"""Cognitive QA analysis — normalization, capture, offline pipeline."""

from nexo_qa.analysis.capture import capture_run_trace
from nexo_qa.analysis.models import CognitiveQAEvent, CognitiveQAObservation, RawRunTrace
from nexo_qa.analysis.normalize import normalize_events
from nexo_qa.analysis.offline import AnalysisResult, analyze_raw_trace, analyze_run, analyze_run_file

__all__ = [
    "AnalysisResult",
    "CognitiveQAEvent",
    "CognitiveQAObservation",
    "RawRunTrace",
    "analyze_raw_trace",
    "analyze_run",
    "analyze_run_file",
    "capture_run_trace",
    "normalize_events",
]
