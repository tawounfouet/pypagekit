from pathlib import Path, PurePosixPath

from pypagekit import (
    Asset,
    Assets,
    Page,
    Paragraph,
    Route,
    Site,
)
from pypagekit.build import StaticSiteGenerator, build_manifest


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



def test_generator_applies_incremental_site_transition(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    generator = StaticSiteGenerator()

    initial_site = Site(
        [
            Route("/", Page("Home", [Paragraph("Before")])),
            Route("/remove", Page("Remove", [Paragraph("Remove me")])),
        ]
    )
    initial = generator.generate(initial_site, output_root)
    previous_manifest = build_manifest(initial.plan)

    next_site = Site(
        [
            Route("/", Page("Home", [Paragraph("After")])),
            Route("/added", Page("Added", [Paragraph("New")])),
        ]
    )

    result = generator.generate_incremental(
        next_site,
        previous_manifest,
        output_root,
    )

    assert result.diff.changed_targets == (PurePosixPath("index.html"),)
    assert result.diff.added_targets == (PurePosixPath("added/index.html"),)
    assert result.diff.removed_targets == (PurePosixPath("remove/index.html"),)
    assert result.written_files == (
        output_root / "index.html",
        output_root / "added" / "index.html",
    )
    assert result.removed_files == (output_root / "remove" / "index.html",)
    assert "After" in (output_root / "index.html").read_text(encoding="utf-8")
    assert "New" in (output_root / "added" / "index.html").read_text(encoding="utf-8")
    assert not (output_root / "remove" / "index.html").exists()
    assert result.files == (
        output_root / "index.html",
        output_root / "added" / "index.html",
    )
