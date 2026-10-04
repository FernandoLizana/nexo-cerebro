"""Flujos de aleatoriedad centralizados y reproducibles."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class RandomStreams:
    """Generadores independientes derivados de una semilla raíz."""

    root_seed: int
    world: np.random.Generator
    neural: np.random.Generator
    sensory: np.random.Generator
    memory: np.random.Generator
    decision: np.random.Generator
    learning: np.random.Generator

    @classmethod
    def from_root_seed(cls, root_seed: int) -> RandomStreams:
        ss = np.random.SeedSequence(int(root_seed) % (2**32))
        child_seeds = ss.spawn(6)
        return cls(
            root_seed=int(root_seed),
            world=np.random.default_rng(child_seeds[0]),
            neural=np.random.default_rng(child_seeds[1]),
            sensory=np.random.default_rng(child_seeds[2]),
            memory=np.random.default_rng(child_seeds[3]),
            decision=np.random.default_rng(child_seeds[4]),
            learning=np.random.default_rng(child_seeds[5]),
        )

    def to_dict(self) -> dict[str, int]:
        return {"root_seed": self.root_seed}
