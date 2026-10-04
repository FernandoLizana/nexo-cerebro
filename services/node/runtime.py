"""Local NEXO Node runtime — start / stop / kill switch (no networking in S2)."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from services.node.capability import CapabilityProfile, build_capability_profile
from services.node.governor import GovernorAction, ResourceGovernor, ResourceLimits, ResourceSample
from services.node.identity import NodeIdentity, load_or_create_identity
from services.node.jobs import JobRejected, JobRequest


class NodeState(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


@dataclass
class NodeRuntime:
    """Voluntary local node process controller.

    S2 scope: identity, capability, governor, allowlisted local jobs, kill switch.
    Networking / coordinator handshakes are intentionally absent.
    """

    data_dir: Path
    node_name: str = "local-node"
    limits: ResourceLimits = field(default_factory=ResourceLimits)
    identity: NodeIdentity | None = None
    capability: CapabilityProfile | None = None
    governor: ResourceGovernor | None = None
    state: NodeState = NodeState.CREATED
    _private_key: Ed25519PrivateKey | None = field(default=None, repr=False)
    _stop_event: threading.Event = field(default_factory=threading.Event, repr=False)
    _active_jobs: dict[str, dict[str, Any]] = field(default_factory=dict, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self) -> None:
        self.data_dir = Path(self.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def state_path(self) -> Path:
        return self.data_dir / "node_state.json"

    def start(self) -> NodeIdentity:
        if self.state is NodeState.RUNNING:
            assert self.identity is not None
            return self.identity
        identity, private_key = load_or_create_identity(self.data_dir, node_name=self.node_name)
        self.identity = identity
        self._private_key = private_key
        self.capability = build_capability_profile(
            cpu_max_percent=self.limits.cpu_max_percent,
            ram_max_mb=self.limits.ram_max_mb,
            gpu_enabled=self.limits.gpu_enabled,
        )
        self.governor = ResourceGovernor(limits=self.limits)
        self._stop_event.clear()
        self.state = NodeState.RUNNING
        self._persist_state(reason="start")
        return identity

    def pause(self) -> None:
        if self.governor is None:
            raise RuntimeError("node not started")
        self.governor.pause()
        self.state = NodeState.PAUSED
        self._persist_state(reason="pause")

    def resume(self) -> None:
        if self.governor is None:
            raise RuntimeError("node not started")
        self.governor.resume()
        if not self._stop_event.is_set():
            self.state = NodeState.RUNNING
        self._persist_state(reason="resume")

    def submit_job(self, request: JobRequest) -> dict[str, Any]:
        if self.state not in (NodeState.RUNNING, NodeState.PAUSED):
            raise RuntimeError(f"node not accepting jobs in state {self.state}")
        if self.governor is None or self.identity is None:
            raise RuntimeError("node not started")
        request.validate()
        if self.state is NodeState.PAUSED or self.governor.limits.paused:
            raise JobRejected("node paused by ResourceGovernor / owner")

        started = time.monotonic()
        with self._lock:
            self._active_jobs[request.job_id] = {
                "job_type": request.job_type,
                "started_at": started,
            }

        try:
            if self._stop_event.is_set():
                raise JobRejected("node stopping")
            sample = self._resource_sample(request, job_elapsed_seconds=0.0)
            action = self.governor.evaluate(sample)
            if action is GovernorAction.TERMINATE_JOB:
                raise JobRejected(f"governor terminated job: {action.value}")
            if action is GovernorAction.PAUSE:
                raise JobRejected("governor paused")

            result = self._execute_local_job(request)
            if self._stop_event.is_set():
                raise JobRejected("node stopped during job")
            if result.get("stopped"):
                raise JobRejected("job cancelled by stop")
            elapsed = time.monotonic() - started
            final = self.governor.evaluate(
                self._resource_sample(request, job_elapsed_seconds=elapsed, prior=sample)
            )
            if final is GovernorAction.TERMINATE_JOB:
                raise JobRejected("governor terminated job after elapsed limit")
            return {
                "ok": True,
                "job_id": request.job_id,
                "job_type": request.job_type,
                "governor": action.value,
                "node_id": self.identity.node_id,
                "result": result,
                "resources": {
                    "cpu_percent": sample.cpu_percent if sample.measured else None,
                    "ram_mb": sample.ram_mb if sample.measured else None,
                    "measured": sample.measured,
                    "unavailable": sample.unavailable,
                },
            }
        finally:
            with self._lock:
                self._active_jobs.pop(request.job_id, None)

    def _resource_sample(
        self,
        request: JobRequest,
        *,
        job_elapsed_seconds: float,
        prior: ResourceSample | None = None,
    ) -> ResourceSample:
        measured = _measure_process_resources()
        if measured is None:
            return ResourceSample(
                cpu_percent=0.0,
                ram_mb=0.0,
                disk_mb=0.0,
                job_elapsed_seconds=job_elapsed_seconds,
                gpu_requested=bool(request.payload.get("gpu", False)),
                measured=False,
                unavailable=True,
            )
        return ResourceSample(
            cpu_percent=float(measured["cpu_percent"]),
            ram_mb=float(measured["ram_mb"]),
            disk_mb=1.0,
            job_elapsed_seconds=job_elapsed_seconds,
            gpu_requested=bool(request.payload.get("gpu", False)),
            measured=True,
            unavailable=False,
        )

    def _execute_local_job(self, request: JobRequest) -> dict[str, Any]:
        if request.job_type == "RUN_NODE_SELF_CHECK":
            assert self.identity is not None and self.capability is not None
            message = f"{self.identity.node_id}:{request.job_id}".encode("utf-8")
            assert self._private_key is not None
            signature = self.identity.sign(self._private_key, message)
            return {
                "self_check": "ok",
                "tier": self.capability.tier.value,
                "signature_hex": signature.hex(),
                "verified": NodeIdentity.verify(
                    self.identity.public_key_pem, message, signature
                ),
            }
        if request.job_type == "CREATE_BEING":
            from services.being.creator import being_public_summary, create_being
            from services.being.store import BeingStore

            assert self.identity is not None
            store = BeingStore(self.data_dir / "beings")
            payload = dict(request.payload)
            being = create_being(
                name=str(payload.get("name") or ""),
                species=str(payload.get("species") or "EXPERIMENTAL"),
                archetype=str(payload.get("archetype") or "CUSTOM"),
                creator_node=self.identity.node_id,
                traits=dict(payload.get("traits") or {}),
                interests=list(payload.get("interests") or []),
                goals=list(payload.get("goals") or []),
                simulated_fears=list(payload.get("simulated_fears") or []),
                preferences=list(payload.get("preferences") or []),
                communication_style=str(payload.get("communication_style") or "neutral"),
                cognitive_budget=float(payload.get("cognitive_budget") or 1.0),
                memory_level=str(payload.get("memory_level") or "standard"),
                use_llm=bool(payload.get("use_llm", False)),
                store=store,
            )
            return {"created": True, "being": being_public_summary(being)}
        if request.job_type == "LIST_BEINGS":
            from services.being.store import BeingStore

            store = BeingStore(self.data_dir / "beings")
            return {"beings": store.list_ids()}
        if request.job_type == "RUN_CREATURE_SIMULATION":
            from services.being.store import BeingStore
            from services.creature.engine import run_creature_ticks

            store = BeingStore(self.data_dir / "beings")
            payload = dict(request.payload)
            being_id = str(payload.get("being_id") or "")
            if not being_id:
                raise JobRejected("RUN_CREATURE_SIMULATION requires being_id")
            being = store.load(being_id)
            ticks = int(payload.get("ticks") or 20)
            seed = int(payload.get("seed") or 0)
            result = run_creature_ticks(
                being,
                ticks=ticks,
                seed=seed,
                should_stop=self._stop_event.is_set,
            )
            if result.get("stopped"):
                return result
            # Persist updated drives/age only when the run finished.
            store.save(being)
            # Keep trajectories bounded in job responses.
            traj = result["trajectory"]
            if len(traj) > 50:
                result = dict(result)
                result["trajectory"] = traj[:10] + traj[-10:]
                result["trajectory_truncated"] = True
            return result
        if request.job_type == "RUN_TEXTWORLD_EXPERIMENT":
            from services.being.store import BeingStore
            from services.worlds.textworld.runner import run_textworld_experiment

            store = BeingStore(self.data_dir / "beings")
            payload = dict(request.payload)
            being_ids = [str(x) for x in list(payload.get("being_ids") or [])]
            if len(being_ids) < 1:
                raise JobRejected("RUN_TEXTWORLD_EXPERIMENT requires being_ids")
            beings = [store.load(i) for i in being_ids]
            ticks = int(payload.get("ticks") or 20)
            seed = int(payload.get("seed") or 0)
            co_locate = payload.get("co_locate")
            initial = None
            if co_locate:
                place = str(co_locate)
                initial = {b.identity.being_id: place for b in beings}
            result = run_textworld_experiment(
                beings,
                seed=seed,
                ticks=ticks,
                initial_places=initial,
                experiment_id=str(payload.get("experiment_id") or request.job_id),
            )
            # Bound event payload size for job responses.
            if len(result["events"]) > 200:
                result = dict(result)
                result["events"] = result["events"][:50] + result["events"][-50:]
                result["events_truncated"] = True
            return result
        # Remaining allowlisted jobs deferred to later Swarm phases.
        return {
            "accepted": True,
            "deferred": True,
            "message": f"{request.job_type} accepted locally; execution deferred to later Swarm phase",
        }

    def kill_switch(self, *, reason: str = "STOP NEXO NODE") -> dict[str, Any]:
        """Visible owner stop: halt jobs, save state, terminate workers. No persistence against uninstall."""
        return self.stop(reason=reason)

    def stop(self, *, reason: str = "stop") -> dict[str, Any]:
        self.state = NodeState.STOPPING
        self._stop_event.set()
        with self._lock:
            cancelled = list(self._active_jobs.keys())
            self._active_jobs.clear()
        # Drop private key from memory intentionally.
        self._private_key = None
        self.state = NodeState.STOPPED
        snapshot = self._persist_state(reason=reason, extra={"cancelled_jobs": cancelled})
        return snapshot

    def _persist_state(self, *, reason: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "state": self.state.value,
            "reason": reason,
            "node_id": None if self.identity is None else self.identity.node_id,
            "node_name": None if self.identity is None else self.identity.node_name,
            "capability": None if self.capability is None else self.capability.to_dict(),
            "limits": self.limits.to_dict(),
            "networking_enabled": False,
            "updated_at": time.time(),
        }
        if extra:
            payload.update(extra)
        self.state_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return payload


def _measure_process_resources() -> dict[str, float] | None:
    """Real process metrics when available; None means unavailable (not synthetic)."""
    try:
        import os

        import psutil

        proc = psutil.Process(os.getpid())
        cpu = float(proc.cpu_percent(interval=0.0))
        ram = float(proc.memory_info().rss) / (1024.0 * 1024.0)
        return {"cpu_percent": cpu, "ram_mb": ram}
    except Exception:
        return None
