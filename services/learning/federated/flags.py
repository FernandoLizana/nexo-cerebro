"""Research opt-in flags — FL is off unless explicitly enabled."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ResearchFlagError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class FederatedResearchFlag:
    """Must be constructed with enabled=True intentionally for any FL session."""

    enabled: bool = False
    acknowledge_risks: bool = False
    purpose: str = "research"

    def validate(self) -> None:
        if self.purpose != "research":
            raise ResearchFlagError("federated learning is research-only in S17")
        if not self.enabled:
            raise ResearchFlagError("federated research flag is disabled (default)")
        if not self.acknowledge_risks:
            raise ResearchFlagError(
                "must acknowledge poisoning/privacy risks before enabling FL research"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "acknowledge_risks": self.acknowledge_risks,
            "purpose": self.purpose,
            "default_enabled": False,
            "auto_deploy_to_core": False,
        }


def require_research_flag(flag: FederatedResearchFlag | None) -> FederatedResearchFlag:
    if flag is None:
        raise ResearchFlagError("missing federated research flag (default is off)")
    flag.validate()
    return flag
