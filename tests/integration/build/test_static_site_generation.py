from pathlib import Path, PurePosixPath

from pypagekit import (
    Asset,
    Assets,
    Page,
    Paragraph,
    Route,
    Site,
)
from pypagekit.build import StaticSiteGenerator


def test_generator_builds_complete_static_site(tmp_path: Path) -> None:
    source = tmp_path / "logo.svg"
    source.write_text("<svg>logo</svg>", encoding="utf-8")

    site = Site(
        [
            Route("/", Page("Home", [Paragraph("Welcome")])),
            Route("/about", Page("About", [Paragraph("About us")])),
        ]
    )
    assets = Assets(
        [
            Asset(
                source,
                PurePosixPath("assets/logo.svg"),
            )
        ]
    )

    result = StaticSiteGenerator().generate(
        site,
        tmp_path / "dist",
        assets=assets,
    )

    assert result.plan.page_targets == (
        PurePosixPath("index.html"),
        PurePosixPath("about/index.html"),
    )
    assert result.plan.asset_targets == (
        PurePosixPath("assets/logo.svg"),
    )
    assert "<title>Home</title>" in (
        tmp_path / "dist" / "index.html"
    ).read_text(encoding="utf-8")
    assert "<p>About us</p>" in (
        tmp_path / "dist" / "about" / "index.html"
    ).read_text(encoding="utf-8")
    assert (
        tmp_path / "dist" / "assets" / "logo.svg"
    ).read_text(encoding="utf-8") == "<svg>logo</svg>"


def test_generator_preserves_plan_and_write_evidence(tmp_path: Path) -> None:
    site = Site([Route("/", Page("Home"))])

    result = StaticSiteGenerator().generate(site, tmp_path / "dist")

    assert result.plan.pages[0].route is site.routes[0]
    assert result.page_files == (tmp_path / "dist" / "index.html",)
    assert result.files == result.write_result.files
