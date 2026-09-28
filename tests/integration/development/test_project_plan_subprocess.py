from pathlib import Path

import pytest

from pypagekit.cli.commands.serve import (
    _ProjectPlanLoadError,
    _load_project_plan,
)


def test_fresh_process_project_plan_reflects_local_module_changes(
    tmp_path: Path,
) -> None:
    (tmp_path / "content.py").write_text(
        'message = "before"\n',
        encoding="utf-8",
    )
    entry = tmp_path / "site.py"
    entry.write_text(
        """
from pypagekit import Page, Paragraph, Route, Site
from content import message

print("project-side output")

site = Site(
    [
        Route(
            "/",
            Page("Home", [Paragraph(message)]),
        )
    ]
)
""".lstrip(),
        encoding="utf-8",
    )

    first = _load_project_plan(tmp_path, entry)
    assert "before" in first.pages[0].content

    (tmp_path / "content.py").write_text(
        'message = "after"\n',
        encoding="utf-8",
    )

    second = _load_project_plan(tmp_path, entry)
    assert "after" in second.pages[0].content
    assert "before" not in second.pages[0].content


def test_project_plan_loader_supports_module_level_assets(tmp_path: Path) -> None:
    asset = tmp_path / "style.css"
    asset.write_text("body{}", encoding="utf-8")
    entry = tmp_path / "site.py"
    entry.write_text(
        """
from pathlib import Path, PurePosixPath

from pypagekit import Asset, Assets, Page, Route, Site

site = Site([Route("/", Page("Home"))])
assets = Assets(
    [
        Asset(
            Path("style.css"),
            PurePosixPath("assets/style.css"),
        )
    ]
)
""".lstrip(),
        encoding="utf-8",
    )

    plan = _load_project_plan(tmp_path, entry)

    assert plan.assets[0].asset.source == asset
    assert plan.assets[0].target.as_posix() == "assets/style.css"


def test_project_plan_loader_rejects_entry_without_site(tmp_path: Path) -> None:
    entry = tmp_path / "site.py"
    entry.write_text("value = 1\n", encoding="utf-8")

    with pytest.raises(_ProjectPlanLoadError, match="module-level 'site'"):
        _load_project_plan(tmp_path, entry)


def test_project_plan_loader_rejects_invalid_assets_value(tmp_path: Path) -> None:
    entry = tmp_path / "site.py"
    entry.write_text(
        """
from pypagekit import Page, Route, Site

site = Site([Route("/", Page("Home"))])
assets = ["not-assets"]
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(_ProjectPlanLoadError, match="module-level 'assets'"):
        _load_project_plan(tmp_path, entry)
