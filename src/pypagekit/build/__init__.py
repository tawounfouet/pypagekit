"""Public build and filesystem output API for PyPageKit."""

from .base import BuildPlannerProtocol
from .filesystem import FilesystemWriteResult, FilesystemWriter
from .generator import StaticSiteGenerationResult, StaticSiteGenerator
from .model import AssetBuildEntry, BuildPlan, PageBuildEntry
from .planner import BuildPlanner, route_output_target

__all__ = [
    "AssetBuildEntry",
    "BuildPlan",
    "BuildPlanner",
    "BuildPlannerProtocol",
    "FilesystemWriteResult",
    "FilesystemWriter",
    "PageBuildEntry",
    "StaticSiteGenerationResult",
    "StaticSiteGenerator",
    "route_output_target",
]
