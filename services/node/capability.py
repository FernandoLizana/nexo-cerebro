"""Capability and hardware profiling for voluntary NEXO nodes."""

from __future__ import annotations

import os
import platform
import shutil
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class NodeTier(str, Enum):
    MICRO = "TIER_0_MICRO"
    LIGHT = "TIER_1_LIGHT"
    STANDARD = "TIER_2_STANDARD"
    ADVANCED = "TIER_3_ADVANCED"
    RESEARCH = "TIER_4_RESEARCH"


@dataclass(frozen=True, slots=True)
class HardwareProfile:
    os_name: str
    architecture: str
    cpu_count: int
    ram_mb_approx: int | None
    available_disk_gb: float | None
    gpu_reported: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CapabilityProfile:
    tier: NodeTier
    hardware: HardwareProfile
    cpu_max_percent: float
    ram_max_mb: int | None
    gpu_enabled: bool
    battery_mode: bool
    savings_mode: bool

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["tier"] = self.tier.value
        payload["hardware"] = self.hardware.to_dict()
        return payload


def _approx_ram_mb() -> int | None:
    """Best-effort RAM estimate without scraping other machines."""
    try:
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return int(stat.ullTotalPhys // (1024 * 1024))
    except Exception:
        pass
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        pages = os.sysconf("SC_PHYS_PAGES")
        return int((page_size * pages) // (1024 * 1024))
    except (AttributeError, OSError, ValueError):
        return None


def detect_hardware(*, gpu_reported: bool = False) -> HardwareProfile:
    disk_gb: float | None
    try:
        usage = shutil.disk_usage(os.path.abspath(os.sep))
        disk_gb = round(usage.free / (1024**3), 2)
    except OSError:
        disk_gb = None
    return HardwareProfile(
        os_name=platform.system(),
        architecture=platform.machine() or "unknown",
        cpu_count=os.cpu_count() or 1,
        ram_mb_approx=_approx_ram_mb(),
        available_disk_gb=disk_gb,
        gpu_reported=bool(gpu_reported),
    )


def infer_tier(hardware: HardwareProfile, *, gpu_enabled: bool = False) -> NodeTier:
    ram = hardware.ram_mb_approx or 0
    cpus = hardware.cpu_count
    if ram and ram < 2048 and cpus <= 2:
        return NodeTier.MICRO
    if ram and ram < 4096:
        return NodeTier.LIGHT
    if gpu_enabled and ram >= 16384 and cpus >= 8:
        return NodeTier.RESEARCH
    if gpu_enabled or (ram >= 8192 and cpus >= 6):
        return NodeTier.ADVANCED
    return NodeTier.STANDARD


def build_capability_profile(
    *,
    cpu_max_percent: float = 50.0,
    ram_max_mb: int | None = None,
    gpu_enabled: bool = False,
    battery_mode: bool = False,
    savings_mode: bool = False,
    gpu_reported: bool = False,
) -> CapabilityProfile:
    hardware = detect_hardware(gpu_reported=gpu_reported)
    tier = infer_tier(hardware, gpu_enabled=gpu_enabled and not battery_mode and not savings_mode)
    if battery_mode or savings_mode:
        tier = NodeTier.MICRO if tier == NodeTier.MICRO else NodeTier.LIGHT
    return CapabilityProfile(
        tier=tier,
        hardware=hardware,
        cpu_max_percent=float(max(1.0, min(100.0, cpu_max_percent))),
        ram_max_mb=ram_max_mb,
        gpu_enabled=bool(gpu_enabled and not battery_mode),
        battery_mode=battery_mode,
        savings_mode=savings_mode,
    )
