"""End-to-end static site generation orchestration."""

from dataclasses import dataclass
from pathlib import Path

from pypagekit.domain import Assets, Site

from .filesystem import FilesystemWriteResult, FilesystemWriter
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


class StaticSiteGenerator:
    """Coordinate build planning and filesystem materialization."""

    def __init__(
        self,
        *,
        planner: BuildPlanner | None = None,
        writer: FilesystemWriter | None = None,
    ) -> None:
        if planner is not None and not isinstance(planner, BuildPlanner):
            raise TypeError(
                "Static site generator planner must be a BuildPlanner or None."
            )
        if writer is not None and not isinstance(writer, FilesystemWriter):
            raise TypeError(
                "Static site generator writer must be a FilesystemWriter or None."
            )

        self._planner = planner if planner is not None else BuildPlanner()
        self._writer = writer if writer is not None else FilesystemWriter()

    @property
    def planner(self) -> BuildPlanner:
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

        plan = self._planner.plan(site, assets)
        write_result = self._writer.write(
            plan,
            output_root,
            overwrite=overwrite,
        )
        return StaticSiteGenerationResult(
            plan=plan,
            write_result=write_result,
        )
