"""Allowlisted job dispatch queue — coordinator never executes jobs itself."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping

from services.node.jobs import ALLOWED_JOB_TYPES, FORBIDDEN_JOB_PREFIXES, JobRejected


@dataclass
class DispatchedJob:
    job_id: str
    job_type: str
    target_node_id: str
    payload: dict[str, Any]
    created_at: float
    status: str = "queued"  # queued | assigned | completed | rejected | cancelled

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "target_node_id": self.target_node_id,
            "payload": dict(self.payload),
            "created_at": self.created_at,
            "status": self.status,
        }


class JobRouter:
    """Queues jobs for nodes. Does not run cognition or shell."""

    def __init__(self) -> None:
        self._jobs: dict[str, DispatchedJob] = {}
        self._queues: dict[str, list[str]] = {}

    def validate_job_type(self, job_type: str) -> None:
        name = str(job_type or "").strip()
        if not name:
            raise JobRejected("empty job_type")
        upper = name.upper()
        for prefix in FORBIDDEN_JOB_PREFIXES:
            if upper.startswith(prefix):
                raise JobRejected(f"forbidden job type: {name}")
        if name not in ALLOWED_JOB_TYPES:
            raise JobRejected(f"job type not allowlisted: {name}")

    def enqueue(
        self,
        *,
        target_node_id: str,
        job_type: str,
        payload: Mapping[str, Any] | None = None,
        job_id: str | None = None,
    ) -> DispatchedJob:
        self.validate_job_type(job_type)
        job = DispatchedJob(
            job_id=job_id or f"job-{uuid.uuid4().hex[:12]}",
            job_type=job_type,
            target_node_id=target_node_id,
            payload=dict(payload or {}),
            created_at=time.time(),
        )
        self._jobs[job.job_id] = job
        self._queues.setdefault(target_node_id, []).append(job.job_id)
        return job

    def poll(self, node_id: str) -> DispatchedJob | None:
        queue = self._queues.get(node_id) or []
        while queue:
            job_id = queue.pop(0)
            job = self._jobs.get(job_id)
            if job is None or job.status != "queued":
                continue
            job.status = "assigned"
            return job
        return None

    def complete(self, job_id: str, *, ok: bool = True) -> None:
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(job_id)
        job.status = "completed" if ok else "rejected"

    def get(self, job_id: str) -> DispatchedJob | None:
        return self._jobs.get(job_id)
