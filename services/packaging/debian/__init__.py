"""Debian/Ubuntu packaging policy (S14) — user-level, no forced root persistence."""

from __future__ import annotations

from services.packaging.debian.layout import DebInstallLayout
from services.packaging.debian.policy import DebianPackagingError, packaging_policy
from services.packaging.debian.unit import user_unit_text

__all__ = [
    "DebInstallLayout",
    "DebianPackagingError",
    "packaging_policy",
    "user_unit_text",
]
