"""Failure episode grouping and merging."""

from __future__ import annotations

from dataclasses import dataclass, field

from nexo_qa.failures.taxonomy import CognitiveFailure, FailureFamily

EPISODE_MERGE_WINDOW = 5


@dataclass
class FailureEpisode:
    episode_id: str
    family: FailureFamily
    failure_types: list[str] = field(default_factory=list)
    failures: list[CognitiveFailure] = field(default_factory=list)
    start_tick: int = 0
    end_tick: int = 0
    recovered: bool = False
    severity: str = "INFO"

    def to_dict(self) -> dict:
        return {
            "episode_id": self.episode_id,
            "family": self.family.value,
            "failure_types": list(self.failure_types),
            "failure_ids": [f.failure_id for f in self.failures],
            "start_tick": self.start_tick,
            "end_tick": self.end_tick,
            "recovered": self.recovered,
            "severity": self.severity,
            "occurrences": len(self.failures),
        }


def merge_failures_into_episodes(failures: list[CognitiveFailure]) -> list[FailureEpisode]:
    """Merge failures by family within temporal window — avoid per-tick spam."""
    if not failures:
        return []
    ordered = sorted(failures, key=lambda f: (f.start_tick, f.failure_id))
    episodes: list[FailureEpisode] = []
    current: FailureEpisode | None = None
    counter = 0

    for fail in ordered:
        if current is None:
            counter += 1
            current = FailureEpisode(
                episode_id=f"ep-{counter:04d}",
                family=fail.family,
                start_tick=fail.start_tick,
                end_tick=fail.end_tick,
                severity=fail.severity,
            )
            current.failures.append(fail)
            current.failure_types.append(fail.failure_type.value)
            if fail.recovered:
                current.recovered = True
            continue

        same_family = fail.family == current.family
        close = fail.start_tick - current.end_tick <= EPISODE_MERGE_WINDOW
        if same_family and close:
            current.failures.append(fail)
            if fail.failure_type.value not in current.failure_types:
                current.failure_types.append(fail.failure_type.value)
            current.end_tick = max(current.end_tick, fail.end_tick)
            if fail.severity in ("HIGH", "CRITICAL"):
                current.severity = fail.severity
            if fail.recovered:
                current.recovered = True
        else:
            episodes.append(current)
            counter += 1
            current = FailureEpisode(
                episode_id=f"ep-{counter:04d}",
                family=fail.family,
                start_tick=fail.start_tick,
                end_tick=fail.end_tick,
                severity=fail.severity,
            )
            current.failures.append(fail)
            current.failure_types.append(fail.failure_type.value)
            if fail.recovered:
                current.recovered = True

    if current is not None:
        episodes.append(current)
    return episodes
