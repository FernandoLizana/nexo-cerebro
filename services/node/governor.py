"""Resource governor — user-configured caps for voluntary nodes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GovernorAction(str, Enum):
    ALLOW = "ALLOW"
    THROTTLE = "THROTTLE"
    PAUSE = "PAUSE"
    TERMINATE_JOB = "TERMINATE_JOB"


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    cpu_max_percent: float = 50.0
    ram_max_mb: int | None = 2048
    gpu_enabled: bool = False
    max_job_seconds: float = 300.0
    max_disk_mb: int | None = 1024
    paused: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "cpu_max_percent": self.cpu_max_percent,
            "ram_max_mb": self.ram_max_mb,
            "gpu_enabled": self.gpu_enabled,
            "max_job_seconds": self.max_job_seconds,
            "max_disk_mb": self.max_disk_mb,
            "paused": self.paused,
        }


@dataclass
class ResourceSample:
    cpu_percent: float = 0.0
    ram_mb: float = 0.0
    disk_mb: float = 0.0
    job_elapsed_seconds: float = 0.0
    gpu_requested: bool = False
    measured: bool = False
    unavailable: bool = False


@dataclass
class ResourceGovernor:
    """Evaluate samples against owner-configured limits."""

    limits: ResourceLimits = field(default_factory=ResourceLimits)

    def pause(self) -> None:
        self.limits = ResourceLimits(
            cpu_max_percent=self.limits.cpu_max_percent,
            ram_max_mb=self.limits.ram_max_mb,
            gpu_enabled=self.limits.gpu_enabled,
            max_job_seconds=self.limits.max_job_seconds,
            max_disk_mb=self.limits.max_disk_mb,
            paused=True,
        )

    def resume(self) -> None:
        self.limits = ResourceLimits(
            cpu_max_percent=self.limits.cpu_max_percent,
            ram_max_mb=self.limits.ram_max_mb,
            gpu_enabled=self.limits.gpu_enabled,
            max_job_seconds=self.limits.max_job_seconds,
            max_disk_mb=self.limits.max_disk_mb,
            paused=False,
        )

    def evaluate(self, sample: ResourceSample) -> GovernorAction:
        if self.limits.paused:
            return GovernorAction.PAUSE
        if sample.gpu_requested and not self.limits.gpu_enabled:
            return GovernorAction.TERMINATE_JOB
        if sample.job_elapsed_seconds > self.limits.max_job_seconds:
            return GovernorAction.TERMINATE_JOB
        if self.limits.ram_max_mb is not None and sample.ram_mb > self.limits.ram_max_mb:
            return GovernorAction.TERMINATE_JOB
        if self.limits.max_disk_mb is not None and sample.disk_mb > self.limits.max_disk_mb:
            return GovernorAction.TERMINATE_JOB
        if sample.cpu_percent > self.limits.cpu_max_percent * 1.25:
            return GovernorAction.TERMINATE_JOB
        if sample.cpu_percent > self.limits.cpu_max_percent:
            return GovernorAction.THROTTLE
        return GovernorAction.ALLOW
