from dataclasses import FrozenInstanceError
from pathlib import Path, PurePosixPath

import pytest

from pypagekit import Asset, Assets, Page, Route, Site
from pypagekit.build import (
    BuildPlan,
    BuildPlanner,
    FilesystemWriteResult,
    FilesystemWriter,
    StaticSiteGenerationResult,
    StaticSiteGenerator,
)
from pypagekit.exceptions import (
    BuildTargetCollisionError,
    ExistingOutputError,
    InvalidBuildPlanError,
)


class RecordingPlanner(BuildPlanner):
    def __init__(self, plan: BuildPlan) -> None:
        super().__init__()
        self.plan_result = plan
        self.calls: list[tuple[Site, Assets | None]] = []

    def plan(self, site: Site, assets: Assets | None = None) -> BuildPlan:
        self.calls.append((site, assets))
        return self.plan_result


class RecordingWriter(FilesystemWriter):
    def __init__(self, result: FilesystemWriteResult) -> None:
        self.result = result
        self.calls: list[tuple[BuildPlan, Path, bool]] = []

    def write(
        self,
        plan: BuildPlan,
        output_root: Path,
        *,
        overwrite: bool = False,
    ) -> FilesystemWriteResult:
        self.calls.append((plan, output_root, overwrite))
        return self.result


def test_generator_exposes_injected_dependencies(tmp_path: Path) -> None:
    plan = BuildPlan()
    write_result = FilesystemWriteResult(tmp_path / "dist", (), ())
    planner = RecordingPlanner(plan)
    writer = RecordingWriter(write_result)

    generator = StaticSiteGenerator(planner=planner, writer=writer)

    assert generator.planner is planner
    assert generator.writer is writer


def test_generator_orchestrates_planner_then_writer(tmp_path: Path) -> None:
    site = Site([Route("/", Page("Home"))])
    assets = Assets()
    plan = BuildPlan()
    output_root = tmp_path / "dist"
    write_result = FilesystemWriteResult(output_root, (), ())
    planner = RecordingPlanner(plan)
    writer = RecordingWriter(write_result)

    result = StaticSiteGenerator(
        planner=planner,
        writer=writer,
    ).generate(
        site,
        output_root,
        assets=assets,
        overwrite=True,
    )

    assert planner.calls == [(site, assets)]
    assert writer.calls == [(plan, output_root, True)]
    assert result.plan is plan
    assert result.write_result is write_result


def test_generation_result_projects_written_files(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    page_file = output_root / "index.html"
    asset_file = output_root / "assets" / "logo.svg"
    write_result = FilesystemWriteResult(
        output_root,
        (page_file,),
        (asset_file,),
    )
    result = StaticSiteGenerationResult(BuildPlan(), write_result)

    assert result.output_root == output_root
    assert result.page_files == (page_file,)
    assert result.asset_files == (asset_file,)
    assert result.files == (page_file, asset_file)


def test_generation_result_is_immutable(tmp_path: Path) -> None:
    result = StaticSiteGenerationResult(
        BuildPlan(),
        FilesystemWriteResult(tmp_path / "dist", (), ()),
    )

    with pytest.raises(FrozenInstanceError):
        result.plan = BuildPlan()  # type: ignore[misc]


def test_generation_result_validates_types(tmp_path: Path) -> None:
    write_result = FilesystemWriteResult(tmp_path / "dist", (), ())

    with pytest.raises(TypeError, match="BuildPlan"):
        StaticSiteGenerationResult("invalid", write_result)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="FilesystemWriteResult"):
        StaticSiteGenerationResult(BuildPlan(), "invalid")  # type: ignore[arg-type]


def test_generator_rejects_invalid_dependencies() -> None:
    with pytest.raises(TypeError, match="BuildPlanner"):
        StaticSiteGenerator(planner=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="FilesystemWriter"):
        StaticSiteGenerator(writer=object())  # type: ignore[arg-type]


def test_generator_propagates_existing_output_policy(tmp_path: Path) -> None:
    site = Site([Route("/", Page("Home"))])
    output_root = tmp_path / "dist"

    generator = StaticSiteGenerator()
    generator.generate(site, output_root)

    with pytest.raises(ExistingOutputError):
        generator.generate(site, output_root)

    result = generator.generate(site, output_root, overwrite=True)
    assert result.output_root == output_root


def test_generator_accepts_assets(tmp_path: Path) -> None:
    source = tmp_path / "logo.svg"
    source.write_text("<svg></svg>", encoding="utf-8")
    assets = Assets(
        [
            Asset(
                source,
                PurePosixPath("assets/logo.svg"),
            )
        ]
    )

    result = StaticSiteGenerator().generate(
        Site(),
        tmp_path / "dist",
        assets=assets,
    )

    assert result.asset_files == (tmp_path / "dist" / "assets" / "logo.svg",)


class FailIfCalledWriter(FilesystemWriter):
    def write(
        self,
        plan: BuildPlan,
        output_root: Path,
        *,
        overwrite: bool = False,
    ) -> FilesystemWriteResult:
        raise AssertionError("writer must not run when planning fails")


def test_generator_does_not_write_when_planning_fails(tmp_path: Path) -> None:
    site = Site(
        [
            Route("/docs", Page("Docs")),
            Route("/docs/index.html", Page("Nested")),
        ]
    )

    with pytest.raises(BuildTargetCollisionError):
        StaticSiteGenerator(writer=FailIfCalledWriter()).generate(
            site,
            tmp_path / "dist",
        )

    assert not (tmp_path / "dist").exists()



class InvalidResultPlanner:
    def plan(self, site: Site, assets: Assets | None = None) -> BuildPlan:
        del site, assets
        return object()  # type: ignore[return-value]


def test_generator_rejects_invalid_third_party_plan_before_writer(
    tmp_path: Path,
) -> None:
    writer = FailIfCalledWriter()

    with pytest.raises(InvalidBuildPlanError, match="expected BuildPlan"):
        StaticSiteGenerator(
            planner=InvalidResultPlanner(),  # type: ignore[arg-type]
            writer=writer,
        ).generate(
            Site(),
            tmp_path / "dist",
        )

    assert not (tmp_path / "dist").exists()
