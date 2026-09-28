"""End-to-end static site generation orchestration."""

from dataclasses import dataclass
from pathlib import Path

from pypagekit.domain import Assets, Site
from pypagekit.exceptions import InvalidBuildPlanError

from .base import BuildPlannerProtocol
from .filesystem import (
    FilesystemWriteResult,
    FilesystemWriter,
    IncrementalFilesystemWriteResult,
)
from .manifest import BuildManifest, BuildManifestDiff
from .model import BuildPlan
from .planner import BuildPlanner


@dataclass(frozen=True, slots=True)
class StaticSiteGenerationResult:
    """Immutable result of planning and materializing one static site."""

    plan: BuildPlan
    write_result: FilesystemWriteResult

    def __post_init__(self) -> None:
        if not isinstance(self.plan, BuildPlan):
            raise TypeError("Static site generation plan must be a BuildPlan object.")
        if not isinstance(self.write_result, FilesystemWriteResult):
            raise TypeError(
                "Static site generation write_result must be a FilesystemWriteResult object."
            )

    @property
    def output_root(self) -> Path:
        """Return the filesystem root used for generation."""

        return self.write_result.output_root

    @property
    def page_files(self) -> tuple[Path, ...]:
        """Return generated page files in plan order."""

        return self.write_result.page_files

    @property
    def asset_files(self) -> tuple[Path, ...]:
        """Return copied asset files in plan order."""

        return self.write_result.asset_files

    @property
    def files(self) -> tuple[Path, ...]:
        """Return every materialized file, pages first then assets."""

        return self.write_result.files


@dataclass(frozen=True, slots=True)
class IncrementalStaticSiteGenerationResult:
    """Immutable result of one incremental static-site generation transition."""

    plan: BuildPlan
    write_result: IncrementalFilesystemWriteResult

    def __post_init__(self) -> None:
        if not isinstance(self.plan, BuildPlan):
            raise TypeError(
                "Incremental static site generation plan must be a BuildPlan object."
            )
        if not isinstance(self.write_result, IncrementalFilesystemWriteResult):
            raise TypeError(
                "Incremental static site generation write_result must be an "
                "IncrementalFilesystemWriteResult object."
            )

    @property
    def output_root(self) -> Path:
        """Return the filesystem root used for incremental generation."""

        return self.write_result.output_root

    @property
    def manifest(self) -> BuildManifest:
        """Return the manifest produced for the resulting build."""

        return self.write_result.manifest

    @property
    def diff(self) -> BuildManifestDiff:
        """Return the manifest diff applied to the filesystem."""

        return self.write_result.diff

    @property
    def files(self) -> tuple[Path, ...]:
        """Return every file represented by the resulting manifest."""

        return self.write_result.files

    @property
    def written_files(self) -> tuple[Path, ...]:
        """Return only files physically written by the incremental transition."""

        return self.write_result.written_files

    @property
    def removed_files(self) -> tuple[Path, ...]:
        """Return files removed by the incremental transition."""

        return self.write_result.removed_files


class StaticSiteGenerator:
    """Coordinate build planning and filesystem materialization."""

    def __init__(
        self,
        *,
        planner: BuildPlannerProtocol | None = None,
        writer: FilesystemWriter | None = None,
    ) -> None:
        if planner is not None and not callable(getattr(planner, "plan", None)):
            raise TypeError(
                "Static site generator planner must satisfy BuildPlannerProtocol or be None."
            )
        if writer is not None and not isinstance(writer, FilesystemWriter):
            raise TypeError(
                "Static site generator writer must be a FilesystemWriter or None."
            )

        self._planner = planner if planner is not None else BuildPlanner()
        self._writer = writer if writer is not None else FilesystemWriter()

    @property
    def planner(self) -> BuildPlannerProtocol:
        """Build planner used by this generator."""

        return self._planner

    @property
    def writer(self) -> FilesystemWriter:
        """Filesystem writer used by this generator."""

        return self._writer

    def generate(
        self,
        site: Site,
        output_root: Path,
        *,
        assets: Assets | None = None,
        overwrite: bool = False,
    ) -> StaticSiteGenerationResult:
        """Plan and materialize a complete static site."""

        plan = self._plan(site, assets)

        write_result = self._writer.write(
            plan,
            output_root,
            overwrite=overwrite,
        )
        return StaticSiteGenerationResult(
            plan=plan,
            write_result=write_result,
        )

    def generate_incremental(
        self,
        site: Site,
        previous_manifest: BuildManifest,
        output_root: Path,
        *,
        assets: Assets | None = None,
    ) -> IncrementalStaticSiteGenerationResult:
        """Plan a site and apply only changes since a previous build manifest."""

        if not isinstance(previous_manifest, BuildManifest):
            raise TypeError(
                "Incremental static site generation previous_manifest must be "
                "a BuildManifest object."
            )

        plan = self._plan(site, assets)
        write_result = self._writer.write_incremental(
            plan,
            previous_manifest,
            output_root,
        )
        return IncrementalStaticSiteGenerationResult(
            plan=plan,
            write_result=write_result,
        )

    def _plan(
        self,
        site: Site,
        assets: Assets | None,
    ) -> BuildPlan:
        plan = self._planner.plan(site, assets)
        if not isinstance(plan, BuildPlan):
            raise InvalidBuildPlanError(
                f"Build planner returned {type(plan).__name__}; expected BuildPlan."
            )
        return plan
