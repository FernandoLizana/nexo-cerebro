"""Global Workspace — selección competitiva de contenido consciente."""

from __future__ import annotations

from dataclasses import dataclass, field

from nexo.workspace.candidate import WorkspaceCandidate

WORKSPACE_CAPACITY = 3

ROOM_ACTION_HINTS: dict[str, tuple[str, ...]] = {
    "food": ("eat",),
    "danger": ("flee",),
    "caregiver": ("approach_caregiver",),
    "distractor": ("inspect_distractor", "explore"),
    "interoception": ("rest", "eat"),
    "hunger": ("eat",),
    "safety": ("flee",),
    "curiosity": ("explore", "inspect_distractor"),
}


@dataclass
class GlobalWorkspace:
    capacity: int = WORKSPACE_CAPACITY
    winners: list[WorkspaceCandidate] = field(default_factory=list)
    suppressed_count: int = 0

    def gather_from_events(
        self,
        *,
        percepts: list[dict],
        drives: dict[str, float],
        focus: tuple[str, ...],
        energy: float,
    ) -> list[WorkspaceCandidate]:
        candidates: list[WorkspaceCandidate] = []

        for p in percepts[-6:]:
            mod = str(p.get("modality", ""))
            sal = float(p.get("salience", 0.3))
            if mod in focus:
                sal = min(1.0, sal + 0.15)
            candidates.append(
                WorkspaceCandidate(
                    source="perception",
                    label=f"{mod}:{sal:.2f}",
                    salience=sal,
                    modality=mod,
                    action_hints=ROOM_ACTION_HINTS.get(mod, ()),
                )
            )

        for drive_name, strength in drives.items():
            if strength < 0.08:
                continue
            candidates.append(
                WorkspaceCandidate(
                    source="drive",
                    label=f"drive:{drive_name}",
                    salience=min(1.0, strength),
                    modality="interoception",
                    action_hints=ROOM_ACTION_HINTS.get(drive_name, ()),
                )
            )

        if energy < 0.35:
            candidates.append(
                WorkspaceCandidate(
                    source="interoception",
                    label="low_energy",
                    salience=min(1.0, (0.35 - energy) * 2.5),
                    modality="interoception",
                    action_hints=("eat", "rest"),
                )
            )

        return candidates

    def select_winners(self, candidates: list[WorkspaceCandidate]) -> list[WorkspaceCandidate]:
        merged: dict[str, WorkspaceCandidate] = {}
        for c in candidates:
            key = c.label.lower()
            if key in merged:
                prev = merged[key]
                merged[key] = WorkspaceCandidate(
                    source=prev.source,
                    label=prev.label,
                    salience=min(1.0, max(prev.salience, c.salience) + c.salience * 0.12),
                    modality=prev.modality or c.modality,
                    valence=prev.valence,
                    action_hints=prev.action_hints or c.action_hints,
                )
            else:
                merged[key] = c
        ranked = sorted(merged.values(), key=lambda x: -x.salience)
        self.suppressed_count = max(0, len(ranked) - self.capacity)
        self.winners = ranked[: max(1, self.capacity)]
        return self.winners

    def action_bias(self) -> dict[str, float]:
        bias: dict[str, float] = {}
        for i, w in enumerate(self.winners):
            weight = w.salience * (1.0 if i == 0 else 0.4)
            for action in w.action_hints:
                bias[action] = min(0.55, bias.get(action, 0.0) + weight * 0.35)
        return bias

    def broadcast_labels(self) -> tuple[str, ...]:
        return tuple(w.label for w in self.winners)
