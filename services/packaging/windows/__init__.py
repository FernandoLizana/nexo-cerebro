"""Windows packaging policy (S13) — consent-first, no silent install."""

from __future__ import annotations

from services.packaging.windows.consent import ConsentError, ConsentRecord, require_consent
from services.packaging.windows.layout import InstallLayout, uninstall_plan
from services.packaging.windows.silent_policy import SilentInstallError, reject_silent_flags

__all__ = [
    "ConsentError",
    "ConsentRecord",
    "InstallLayout",
    "SilentInstallError",
    "reject_silent_flags",
    "require_consent",
    "uninstall_plan",
]
