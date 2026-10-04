"""Bind policy for the experimental mobile lab gateway."""

from __future__ import annotations

import ipaddress


def assert_explicit_private_host(host: str, *, allow_loopback: bool = False) -> str:
    raw = str(host or "").strip()
    if raw in {"", "0.0.0.0", "::", "[::]"}:
        raise ValueError("refusing wildcard bind; pass an explicit private IP")
    try:
        ip = ipaddress.ip_address(raw)
    except ValueError as exc:
        raise ValueError(f"host must be an IP address, not a name: {raw}") from exc
    if ip.is_multicast or ip.is_unspecified or (ip.is_reserved and not ip.is_private and not ip.is_loopback):
        raise ValueError(f"refusing non-private bind: {raw}")
    if ip.is_loopback:
        if not allow_loopback:
            raise ValueError("loopback requires --allow-loopback (tests or adb reverse only)")
        return raw
    if not ip.is_private:
        raise ValueError(f"refusing public bind: {raw}")
    return raw


def flags_required(enable_mobile_lab: bool, acknowledge_risks: bool) -> str | None:
    if not enable_mobile_lab or not acknowledge_risks:
        return "refusing to start: pass --enable-mobile-lab and --acknowledge-risks"
    return None
