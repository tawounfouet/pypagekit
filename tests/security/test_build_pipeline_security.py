from pathlib import Path, PurePosixPath

import pytest

from pypagekit import Asset, Assets, Page, Paragraph, Route, Site
from pypagekit.build import BuildPlanner
from pypagekit.exceptions import BuildTargetCollisionError, InvalidBuildTargetError


def test_build_pipeline_preserves_renderer_escaping() -> None:
    site = Site(
        [
            Route(
                "/",
                Page("Safe", [Paragraph("<script>alert(1)</script>")]),
            )
        ]
    )

    html = BuildPlanner().plan(site).pages[0].content

    assert "<script" not in html.lower()
    assert "&lt;script&gt;" in html


def test_build_pipeline_rejects_route_that_maps_to_nonportable_target() -> None:
    site = Site([Route("/bad:name", Page("Bad"))])

    with pytest.raises(InvalidBuildTargetError):
        BuildPlanner().plan(site)


def test_build_pipeline_rejects_asset_collision_with_page_target() -> None:
    site = Site([Route("/assets/app.css", Page("Page"))])
    assets = Assets(
        [
            Asset(
                Path("app.css"),
                PurePosixPath("assets/app.css/index.html"),
            )
        ]
    )

    with pytest.raises(BuildTargetCollisionError):
        BuildPlanner().plan(site, assets)


def test_build_pipeline_performs_no_filesystem_write() -> None:
    missing = Path("/definitely/not/present/app.css")
    assets = Assets(
        [Asset(missing, PurePosixPath("assets/app.css"))]
    )

    plan = BuildPlanner().plan(Site(), assets)

    assert plan.assets[0].asset.source is missing
