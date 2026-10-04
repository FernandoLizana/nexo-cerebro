"""Multi-device lab session — ≥2 nodes, allowlisted jobs, reproducible IDs."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from protocols.events.codec import encode_event
from services.coordinator.auth import heartbeat_message, registration_message
from services.coordinator.service import Coordinator
from services.lab.experiment_id import make_experiment_id
from services.lab.faults import run_fault_battery
from services.lab.killswitch import verify_kill_switch
from services.lab.tls_policy import TlsLabPolicy
from services.node.identity import load_or_create_identity
from services.node.jobs import ALLOWED_JOB_TYPES
from services.worlds.textworld.runner import run_textworld_experiment
from services.being.creator import create_being
from services.being.store import BeingStore


class LabError(ValueError):
    pass


@dataclass
class MultiDeviceLabSession:
    """In-process rehearsal for a voluntary ≥2-device lab (S15).

    Physical TLS links are required for real devices (see runbook).
    This session never enables remote shell jobs or federated learning.
    """

    root: Path
    lab_name: str = "s15-lab"
    seed: int = 15
    tls: TlsLabPolicy = field(default_factory=TlsLabPolicy)
    min_devices: int = 2

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.tls.validate()
        if self.min_devices < 2:
            raise LabError("S15 requires at least 2 devices")

    def rehearse(self) -> dict[str, Any]:
        """Register two nodes, run allowlisted TextWorld job path, verify kill switches + faults."""
        coord = Coordinator(heartbeat_timeout_s=30.0)
        devices: list[dict[str, Any]] = []
        identities = []
        keys = []
        for i in range(self.min_devices):
            ddir = self.root / f"device_{i}"
            identity, private_key = load_or_create_identity(ddir, node_name=f"lab-device-{i}")
            ch = coord.begin_registration(identity.node_id)
            sig = identity.sign(
                private_key,
                registration_message(identity.node_id, identity.node_name, ch["nonce"]),
            )
            coord.register_node(
                node_id=identity.node_id,
                node_name=identity.node_name,
                public_key_pem=identity.public_key_pem,
                software_version=identity.software_version,
                signature=sig,
            )
            ts = time.time()
            coord.heartbeat(
                node_id=identity.node_id,
                seq=1,
                ts=ts,
                signature=identity.sign(
                    private_key, heartbeat_message(identity.node_id, 1, ts)
                ),
                now=ts,
            )
            identities.append(identity)
            keys.append(private_key)
            devices.append({"node_id": identity.node_id, "name": identity.node_name, "data_dir": str(ddir)})

        experiment_id = make_experiment_id(
            lab_name=self.lab_name,
            seed=self.seed,
            device_ids=[d["node_id"] for d in devices],
            protocol="textworld",
        )
        # Create two beings and run a tiny textworld experiment (allowlisted science path)
        beings_root = self.root / "beings"
        store = BeingStore(beings_root)
        b0 = create_being(
            name="LabA",
            species="EXPERIMENTAL",
            creator_node=identities[0].node_id,
            store=store,
        )
        b1 = create_being(
            name="LabB",
            species="EXPERIMENTAL",
            creator_node=identities[1].node_id,
            store=store,
        )
        tw = run_textworld_experiment(
            [b0, b1],
            seed=self.seed,
            ticks=5,
            experiment_id=experiment_id,
        )

        job = coord.dispatch_job(
            target_node_id=identities[0].node_id,
            job_type="RUN_NODE_SELF_CHECK",
            payload={"experiment_id": experiment_id},
        )
        assert job.job_type in ALLOWED_JOB_TYPES

        # Quarantined event from device 0
        ev = encode_event(
            event_type="EXPERIMENT_COMPLETED",
            tick=5,
            payload={"experiment_id": experiment_id, "ticks": 5},
        )
        ingested = coord.ingest_event(source_node_id=identities[0].node_id, event=ev)
        assert ingested["quarantined"] is True

        kill_results = [
            verify_kill_switch(self.root / f"kill_{i}", node_name=f"kill-{i}")
            for i in range(self.min_devices)
        ]
        faults = run_fault_battery(self.root / "faults")
        if not all(f.ok for f in faults):
            raise LabError(f"fault battery failed: {[f.to_dict() for f in faults if not f.ok]}")

        return {
            "ok": True,
            "lab_name": self.lab_name,
            "experiment_id": experiment_id,
            "devices": devices,
            "device_count": len(devices),
            "tls": self.tls.to_dict(),
            "textworld": {
                "experiment_id": tw["experiment"]["experiment_id"],
                "ticks": tw["experiment"]["ticks"],
                "trace_fingerprint": tw.get("trace_fingerprint"),
            },
            "job_dispatched": job.job_type,
            "event_quarantined": True,
            "kill_switches": kill_results,
            "faults": [f.to_dict() for f in faults],
            "federated_learning": False,
            "networking_enabled": False,
            "cognition_on_coordinator": False,
            "note": (
                "In-process rehearsal complete. For physical devices follow "
                "docs/experiments/S15_MULTI_DEVICE_LAB.md with TLS."
            ),
        }
