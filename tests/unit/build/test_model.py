from dataclasses import FrozenInstanceError
from pathlib import Path, PurePosixPath

import pytest

from pypagekit import Asset, Page, Route
from pypagekit.build import AssetBuildEntry, BuildPlan, PageBuildEntry
from pypagekit.exceptions import (
    BuildTargetCollisionError,
    InvalidBuildContentError,
    InvalidBuildTargetError,
)


def page_entry(path: str, target: str) -> PageBuildEntry:
    return PageBuildEntry(
        Route(path, Page(path)),
        PurePosixPath(target),
        "<html></html>",
    )


def test_page_build_entry_preserves_route_target_and_content() -> None:
    route = Route("/about", Page("About"))
    entry = PageBuildEntry(
        route,
        PurePosixPath("about/index.html"),
        "<!DOCTYPE html>",
    )

    assert entry.route is route
    assert entry.target == PurePosixPath("about/index.html")
    assert entry.content == "<!DOCTYPE html>"


def test_page_build_entry_rejects_non_string_content() -> None:
    with pytest.raises(InvalidBuildContentError):
        PageBuildEntry(
            Route("/", Page("Home")),
            PurePosixPath("index.html"),
            42,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "target",
    [
        PurePosixPath("/index.html"),
        PurePosixPath("../index.html"),
        PurePosixPath("bad:name/index.html"),
        PurePosixPath("bad%2Fname/index.html"),
    ],
)
def test_page_build_entry_rejects_unsafe_target(target: PurePosixPath) -> None:
    with pytest.raises(InvalidBuildTargetError):
        PageBuildEntry(Route("/", Page("Home")), target, "html")


def test_asset_build_entry_exposes_asset_target() -> None:
    asset = Asset(Path("logo.png"), PurePosixPath("assets/logo.png"))
    entry = AssetBuildEntry(asset)

    assert entry.asset is asset
    assert entry.target == PurePosixPath("assets/logo.png")


def test_build_plan_can_be_empty() -> None:
    plan = BuildPlan()

    assert plan.pages == ()
    assert plan.assets == ()
    assert plan.targets == ()


def test_build_plan_preserves_page_then_asset_target_order() -> None:
    page = page_entry("/", "index.html")
    asset = AssetBuildEntry(
        Asset(Path("app.css"), PurePosixPath("assets/app.css"))
    )

    plan = BuildPlan([page], [asset])

    assert plan.page_targets == (PurePosixPath("index.html"),)
    assert plan.asset_targets == (PurePosixPath("assets/app.css"),)
    assert plan.targets == (
        PurePosixPath("index.html"),
        PurePosixPath("assets/app.css"),
    )


def test_build_plan_rejects_exact_page_asset_collision() -> None:
    page = page_entry("/", "index.html")
    asset = AssetBuildEntry(
        Asset(Path("source.txt"), PurePosixPath("index.html"))
    )

    with pytest.raises(BuildTargetCollisionError):
        BuildPlan([page], [asset])


def test_build_plan_rejects_file_directory_collision() -> None:
    page = page_entry("/docs", "docs/index.html")
    asset = AssetBuildEntry(
        Asset(Path("docs.bin"), PurePosixPath("docs"))
    )

    with pytest.raises(BuildTargetCollisionError):
        BuildPlan([page], [asset])


def test_build_plan_rejects_inverse_file_directory_collision() -> None:
    page = page_entry("/docs", "docs/index.html")
    asset = AssetBuildEntry(
        Asset(
            Path("nested.bin"),
            PurePosixPath("docs/index.html/nested.bin"),
        )
    )

    with pytest.raises(BuildTargetCollisionError):
        BuildPlan([page], [asset])


def test_build_plan_allows_sibling_files_in_same_directory() -> None:
    first = AssetBuildEntry(
        Asset(Path("a.css"), PurePosixPath("assets/a.css"))
    )
    second = AssetBuildEntry(
        Asset(Path("b.css"), PurePosixPath("assets/b.css"))
    )

    plan = BuildPlan(assets=[first, second])

    assert plan.asset_targets == (
        PurePosixPath("assets/a.css"),
        PurePosixPath("assets/b.css"),
    )


def test_build_plan_is_immutable() -> None:
    plan = BuildPlan()

    with pytest.raises(FrozenInstanceError):
        plan.pages = ()  # type: ignore[misc]
