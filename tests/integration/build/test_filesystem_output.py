from pathlib import Path, PurePosixPath

from pypagekit import Asset, Assets, Page, Paragraph, Route, Site
from pypagekit.build import BuildPlanner, FilesystemWriter


def test_build_plan_materializes_complete_static_tree(tmp_path: Path) -> None:
    source = tmp_path / "logo.svg"
    source.write_text("<svg></svg>", encoding="utf-8")

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

    plan = BuildPlanner().plan(site, assets)
    output_root = tmp_path / "dist"
    result = FilesystemWriter().write(plan, output_root)

    assert (output_root / "index.html").is_file()
    assert (output_root / "about" / "index.html").is_file()
    assert (output_root / "assets" / "logo.svg").is_file()

    assert "<title>Home</title>" in (output_root / "index.html").read_text(
        encoding="utf-8"
    )
    assert "<p>About us</p>" in (
        output_root / "about" / "index.html"
    ).read_text(encoding="utf-8")
    assert (output_root / "assets" / "logo.svg").read_text(
        encoding="utf-8"
    ) == "<svg></svg>"

    assert result.page_files == (
        output_root / "index.html",
        output_root / "about" / "index.html",
    )
    assert result.asset_files == (output_root / "assets" / "logo.svg",)


def test_existing_output_tree_can_be_updated_only_explicitly(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    first_plan = BuildPlanner().plan(
        Site([Route("/", Page("First"))])
    )
    second_plan = BuildPlanner().plan(
        Site([Route("/", Page("Second"))])
    )

    writer = FilesystemWriter()
    writer.write(first_plan, output_root)
    writer.write(second_plan, output_root, overwrite=True)

    html = (output_root / "index.html").read_text(encoding="utf-8")
    assert "<title>Second</title>" in html
