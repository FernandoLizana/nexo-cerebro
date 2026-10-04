"""EHFP — NEXO Estimated Human Failure Proxy (NOT a probability)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nexo_qa.analysis.models import RawRunTrace
from nexo_qa.failures.episodes import FailureEpisode
from nexo_qa.failures.taxonomy import CognitiveFailure
from nexo_qa.metrics.models import MetricResult

EHFP_VERSION = "ehfp_v1"


@dataclass
class EHFPResult:
    version: str = EHFP_VERSION
    value: float | None = None
    label: str = "moderate simulation failure propensity"
    is_probability: bool = False
    disclaimer: str = "EHFP IS NOT A PROBABILITY IN P6"
    inputs: dict[str, float] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.inputs is None:
            self.inputs = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "value": None if self.value is None else round(self.value, 2),
            "label": self.label,
            "is_probability": False,
            "disclaimer": self.disclaimer,
            "inputs": {k: round(v, 4) for k, v in self.inputs.items()},
        }


def compute_ehfp(
    raw: RawRunTrace,
    failures: list[CognitiveFailure],
    episodes: list[FailureEpisode],
) -> EHFPResult:
    progress = raw.metadata.get("final_progress") or {}
    level = str(progress.get("level", "none"))
    terminal = 1.0 if level in ("none", "blocked") and raw.ticks > 5 else 0.0
    sev_high = sum(1 for f in failures if f.severity in ("HIGH", "CRITICAL")) / max(1, len(failures))
    stagnation = sum(1 for ep in episodes if "STAGNATION" in ep.failure_types or "NO_PROGRESS" in ep.failure_types)
    stagnation_n = min(1.0, stagnation / 3.0)
    attn = sum(1 for f in failures if f.family.value == "ATTENTION") / max(1, len(failures))
    raw_score = terminal * 0.35 + sev_high * 0.25 + stagnation_n * 0.25 + attn * 0.15
    value = min(100.0, max(0.0, raw_score * 100.0))
    if value <= 20:
        label = "low simulation failure propensity"
    elif value <= 40:
        label = "low-moderate simulation failure propensity"
    elif value <= 60:
        label = "moderate simulation failure propensity"
    elif value <= 80:
        label = "high simulation failure propensity"
    else:
        label = "very high simulation failure propensity"
    return EHFPResult(value=value, label=label, inputs={
        "terminal_failure": terminal,
        "severity_high_rate": sev_high,
        "stagnation": stagnation_n,
        "attention_failure_rate": attn,
    })


def ehfp_metric_result(ehfp: EHFPResult) -> MetricResult:
    return MetricResult(
        metric_id="ehfp_v1",
        value=ehfp.value,
        status="AVAILABLE",
        coverage=1.0,
        version=EHFP_VERSION,
        metadata=ehfp.to_dict(),
    )
