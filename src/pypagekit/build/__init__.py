"""Public build and filesystem output API for PyPageKit."""

from .base import BuildPlannerProtocol
from .filesystem import (
    FilesystemWriteResult,
    FilesystemWriter,
    IncrementalFilesystemWriteResult,
)
from .generator import (
    IncrementalStaticSiteGenerationResult,
    StaticSiteGenerationResult,
    StaticSiteGenerator,
)
from .manifest import (
    BuildFingerprint,
    BuildManifest,
    BuildManifestDiff,
    BuildManifestEntry,
    build_manifest,
    diff_build_manifests,
)
from .model import AssetBuildEntry, BuildPlan, PageBuildEntry
from .planner import BuildPlanner, route_output_target

__all__ = [
    "AssetBuildEntry",
    "BuildFingerprint",
    "BuildManifest",
    "BuildManifestDiff",
    "BuildManifestEntry",
    "BuildPlan",
    "BuildPlanner",
    "BuildPlannerProtocol",
    "FilesystemWriteResult",
    "FilesystemWriter",
    "IncrementalFilesystemWriteResult",
    "IncrementalStaticSiteGenerationResult",
    "PageBuildEntry",
    "StaticSiteGenerationResult",
    "StaticSiteGenerator",
    "build_manifest",
    "diff_build_manifests",
    "route_output_target",
]
