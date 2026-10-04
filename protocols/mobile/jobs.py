"""Mobile job allowlist. Types reuse services.node.jobs where they already exist."""

from __future__ import annotations

from services.node.jobs import ALLOWED_JOB_TYPES, FORBIDDEN_JOB_PREFIXES

# Extra control jobs the phone may accept. They are not shell and do not run cognition on the PC.
MOBILE_CONTROL_JOBS = frozenset(
    {
        "GET_NODE_STATUS",
        "PAUSE_NODE",
        "RESUME_NODE",
        "STOP_EXPERIMENT",
    }
)

MOBILE_TIER0_JOBS = frozenset(
    {
        "RUN_CREATURE_SIMULATION",
        "RUN_TEXTWORLD_EXPERIMENT",
        "RUN_BEING_INTERACTION",
        "CREATE_BEING",
        "LIST_BEINGS",
    }
) | MOBILE_CONTROL_JOBS

# Blocked even if a future Core allowlist grows. Keep the word "forbidden" so scanners stay honest.
FORBIDDEN_MOBILE_JOBS = frozenset(
    {
        "EXECUTE_SHELL",
        "INSTALL_PACKAGE",
        "OPEN_URL",
        "READ_PATH",
        "WRITE_PATH",
        "UPLOAD_FILE",
        "DOWNLOAD_FILE",
        "SCAN_NETWORK",
        "READ_CONTACTS",
        "READ_MESSAGES",
        "READ_LOCATION",
        "CAPTURE_AUDIO",
        "CAPTURE_CAMERA",
        "CAPTURE_SCREEN",
        "ACCESS_CLIPBOARD",
    }
)


def mobile_job_allowed(job_type: str, declared: set[str] | frozenset[str]) -> str | None:
    """Return an error string, or None if the job may be queued for this node."""
    name = str(job_type or "").strip()
    upper = name.upper()
    if not name:
        return "empty job_type"
    if name in FORBIDDEN_MOBILE_JOBS or upper in FORBIDDEN_MOBILE_JOBS:
        return f"forbidden job type: {name}"
    for prefix in FORBIDDEN_JOB_PREFIXES:
        if upper.startswith(prefix):
            return f"forbidden job prefix: {name}"
    if name in MOBILE_CONTROL_JOBS:
        return None
    if name not in MOBILE_TIER0_JOBS:
        return f"job type not allowlisted for mobile tier 0: {name}"
    if name not in ALLOWED_JOB_TYPES:
        return f"job type not allowlisted: {name}"
    if name not in declared:
        return f"node did not declare job: {name}"
    return None
