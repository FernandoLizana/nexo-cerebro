"""Ablaciones sistemáticas sobre capas integradas."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nexo.integrated_runtime import IntegratedRuntimeConfig


@dataclass(frozen=True)
class AblationProfile:
    ablation_id: str
    label: str
    memory_mode: str | None = None
    executive_mode: str | None = None
    learning_mode: str | None = None
    consciousness_mode: str | None = None
    social_mode: str | None = None
    sleep_mode: str | None = None
    evaluation_mode: str | None = None
    disable_processes: tuple[str, ...] = ()

    def apply(self, cfg: IntegratedRuntimeConfig) -> IntegratedRuntimeConfig:
        patch: dict[str, Any] = {}
        for key in (
            "memory_mode",
            "executive_mode",
            "learning_mode",
            "consciousness_mode",
            "social_mode",
            "sleep_mode",
            "evaluation_mode",
        ):
            val = getattr(self, key)
            if val is not None:
                patch[key] = val
        if self.disable_processes:
            merged = tuple(dict.fromkeys(cfg.disable_processes + self.disable_processes))
            patch["disable_processes"] = merged
        patch["profile"] = f"{cfg.profile}_{self.ablation_id}"
        return replace(cfg, **patch)


INTEGRATED_FULL = AblationProfile("integrated_full", "Stack completo integrado")

ABLATION_REGISTRY: dict[str, AblationProfile] = {
    "integrated_full": INTEGRATED_FULL,
    "abl_no_memory": AblationProfile("abl_no_memory", "Sin memoria integrada", memory_mode="legacy"),
    "abl_no_executive": AblationProfile("abl_no_executive", "Sin ejecutivo integrado", executive_mode="legacy"),
    "abl_no_learning": AblationProfile("abl_no_learning", "Sin aprendizaje integrado", learning_mode="legacy"),
    "abl_no_consciousness": AblationProfile(
        "abl_no_consciousness", "Sin workspace/metacognición", consciousness_mode="legacy"
    ),
    "abl_no_social": AblationProfile("abl_no_social", "Sin cognición social", social_mode="legacy"),
    "abl_no_sleep": AblationProfile("abl_no_sleep", "Sin sueño/consolidación", sleep_mode="legacy"),
    "abl_no_pfc": AblationProfile(
        "abl_no_pfc",
        "Sin deliberación PFC",
        disable_processes=("prefrontal_deliberation",),
    ),
}


def list_ablations() -> list[AblationProfile]:
    return list(ABLATION_REGISTRY.values())
