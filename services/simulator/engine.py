"""Discrete-event Swarm Simulator engine (in-process only)."""

from __future__ import annotations

import heapq
import random
import time
from typing import Any

from services.knowledge.memory import InMemoryKnowledgeGraph
from services.knowledge.service import record_interaction
from services.simulator.clock import SimClock
from services.simulator.events import SimEvent, SimEventKind
from services.simulator.metrics import SimMetrics, social_degree_stats
from services.simulator.node import LogicalNode


class SimulatorError(ValueError):
    pass


class DiscreteEventSimulator:
    """Event-driven logical swarm — shared clock, no sockets, no OS processes per node."""

    def __init__(
        self,
        *,
        n_nodes: int = 10,
        beings_per_node: int = 2,
        seed: int = 42,
        memory_budget_bytes: int = 64_000_000,
        avg_degree: int = 3,
    ) -> None:
        if n_nodes < 1:
            raise SimulatorError("n_nodes must be >= 1")
        if n_nodes > 50_000:
            raise SimulatorError("n_nodes exceeds hard safety cap (50000)")
        self.rng = random.Random(int(seed))
        self.clock = SimClock()
        self.memory_budget_bytes = int(memory_budget_bytes)
        self._queue: list[SimEvent] = []
        self.peak_queue = 0
        self.events_processed = 0
        self.interactions = 0
        self.graph = InMemoryKnowledgeGraph()
        self._social: dict[str, set[str]] = {}
        self.nodes: dict[str, LogicalNode] = {}
        self._build_topology(n_nodes, beings_per_node, avg_degree=avg_degree)

    def _build_topology(self, n_nodes: int, beings_per_node: int, *, avg_degree: int) -> None:
        ids = [f"sim-node-{i:05d}" for i in range(n_nodes)]
        for i, nid in enumerate(ids):
            beings = [f"being:{nid}:{b}" for b in range(max(0, beings_per_node))]
            self.nodes[nid] = LogicalNode(node_id=nid, beings=beings)
            for bid in beings:
                self.graph.upsert_node(kind="BEING", node_id=bid, label=bid)
            self.graph.upsert_node(kind="NODE", node_id=nid, label=nid)

        # Ring + random shortcuts → sparse social/network graph without sockets
        deg = max(1, min(avg_degree, max(1, n_nodes - 1)))
        for i, nid in enumerate(ids):
            neighbors: set[str] = set()
            neighbors.add(ids[(i + 1) % n_nodes])
            while len(neighbors) < deg and n_nodes > 1:
                neighbors.add(ids[self.rng.randrange(n_nodes)])
            neighbors.discard(nid)
            self.nodes[nid].neighbors = sorted(neighbors)

    def schedule(self, event: SimEvent) -> None:
        if event.time < self.clock.now:
            raise SimulatorError("cannot schedule event in the past")
        heapq.heappush(self._queue, event)
        self.peak_queue = max(self.peak_queue, len(self._queue))

    def seed_workload(self, *, horizon: float = 50.0, interacts_per_node: int = 2) -> None:
        """Schedule heartbeats + pairwise interactions across the horizon."""
        for node in self.nodes.values():
            t = self.rng.uniform(0.0, max(0.1, horizon * 0.2))
            self.schedule(
                SimEvent(
                    time=t,
                    kind=SimEventKind.HEARTBEAT,
                    source_id=node.node_id,
                    payload={"seq": 1},
                )
            )
            for _ in range(max(0, interacts_per_node)):
                if len(node.beings) < 1 or not node.neighbors:
                    continue
                peer = self.rng.choice(node.neighbors)
                peer_node = self.nodes[peer]
                if not peer_node.beings:
                    continue
                a = self.rng.choice(node.beings)
                b = self.rng.choice(peer_node.beings)
                ti = self.rng.uniform(0.0, horizon)
                self.schedule(
                    SimEvent(
                        time=ti,
                        kind=SimEventKind.INTERACT,
                        source_id=node.node_id,
                        target_id=peer,
                        payload={"being_a": a, "being_b": b},
                    )
                )

    def _handle(self, event: SimEvent) -> None:
        if event.kind is SimEventKind.HEARTBEAT:
            node = self.nodes.get(event.source_id)
            if node:
                node.heartbeats += 1
            return
        if event.kind is SimEventKind.INTERACT:
            src = self.nodes.get(event.source_id)
            dst = self.nodes.get(event.target_id or "")
            if not src or not dst:
                return
            a = str(event.payload.get("being_a") or "")
            b = str(event.payload.get("being_b") or "")
            if not a or not b:
                return
            record_interaction(self.graph, a, b, confidence=0.5, props={"sim_time": event.time})
            self._social.setdefault(a, set()).add(b)
            self._social.setdefault(b, set()).add(a)
            src.interactions += 1
            dst.interactions += 1
            src.inbox_size += 1
            dst.inbox_size += 1
            self.interactions += 1
            return
        if event.kind is SimEventKind.BROADCAST:
            src = self.nodes.get(event.source_id)
            if not src:
                return
            for nb in src.neighbors:
                peer = self.nodes[nb]
                peer.inbox_size += 1
            return
        # TICK / KNOWLEDGE_GOSSIP: counted only
        return

    def run_until(self, horizon: float) -> SimMetrics:
        wall0 = time.perf_counter()
        while self._queue and self._queue[0].time <= horizon:
            event = heapq.heappop(self._queue)
            self.clock.advance_to(event.time)
            self._handle(event)
            self.events_processed += 1
        if self.clock.now < horizon and not self._queue:
            self.clock.advance_to(horizon)
        wall = time.perf_counter() - wall0
        return self.metrics(wall_seconds=wall)

    def estimated_bytes(self) -> int:
        total = 1024 + 64 * len(self._queue)
        for node in self.nodes.values():
            total += node.estimate_bytes()
        # Social adjacency + KG rough
        total += 48 * sum(len(v) for v in self._social.values())
        total += 128 * self.graph.stats()["nodes"] + 96 * self.graph.stats()["edges"]
        return int(total)

    def metrics(self, *, wall_seconds: float = 0.0) -> SimMetrics:
        mean_deg, max_deg, edges = social_degree_stats(self._social)
        est = self.estimated_bytes()
        beings = sum(len(n.beings) for n in self.nodes.values())
        return SimMetrics(
            nodes=len(self.nodes),
            beings=beings,
            events_processed=self.events_processed,
            sim_time=self.clock.now,
            wall_seconds=float(wall_seconds),
            peak_queue=self.peak_queue,
            estimated_bytes=est,
            memory_budget_bytes=self.memory_budget_bytes,
            within_memory_budget=est <= self.memory_budget_bytes,
            interactions=self.interactions,
            social_edges=edges,
            mean_degree=mean_deg,
            max_degree=max_deg,
            extras={"queue_remaining": len(self._queue)},
        )

    def status(self) -> dict[str, Any]:
        m = self.metrics()
        return {
            "networking_enabled": False,
            "os_processes_per_node": False,
            "backend": "discrete_event_in_process",
            "metrics": m.to_dict(),
        }
