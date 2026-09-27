"""Public structural contracts for build planning."""

from typing import Protocol

from pypagekit.domain import Assets, Site

from .model import BuildPlan


class BuildPlannerProtocol(Protocol):
    """Structural contract consumed by StaticSiteGenerator."""

    def plan(
        self,
        site: Site,
        assets: Assets | None = None,
    ) -> BuildPlan:
        """Create a deterministic build plan."""
        ...


__all__ = ["BuildPlannerProtocol"]
