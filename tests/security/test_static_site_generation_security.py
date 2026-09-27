from pathlib import Path, PurePosixPath

import pytest

from pypagekit import Asset, Assets, Page, Route, Site
from pypagekit.build import StaticSiteGenerator
from pypagekit.exceptions import (
    BuildTargetCollisionError,
    OutputSymlinkError,
)


def test_generator_preserves_build_target_collision_protection(
    tmp_path: Path,
) -> None:
    site = Site([Route("/", Page("Home"))])
    source = tmp_path / "index.html"
    source.write_text("asset", encoding="utf-8")
    assets = Assets(
        [
            Asset(
                source,
                PurePosixPath("index.html"),
            )
        ]
    )

    with pytest.raises(BuildTargetCollisionError):
        StaticSiteGenerator().generate(
            site,
            tmp_path / "dist",
            assets=assets,
        )

    assert not (tmp_path / "dist").exists()


def test_generator_preserves_filesystem_symlink_protection(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    output_root = tmp_path / "dist"
    output_root.symlink_to(outside, target_is_directory=True)

    with pytest.raises(OutputSymlinkError):
        StaticSiteGenerator().generate(
            Site([Route("/", Page("Home"))]),
            output_root,
        )

    assert list(outside.iterdir()) == []
