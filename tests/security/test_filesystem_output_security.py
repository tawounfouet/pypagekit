from pathlib import Path, PurePosixPath

import pytest

from pypagekit import Asset, Page, Route
from pypagekit.build import AssetBuildEntry, BuildPlan, FilesystemWriter, PageBuildEntry
from pypagekit.exceptions import (
    AssetSourceOutputConflictError,
    OutputPathConflictError,
    OutputSymlinkError,
)


def test_symlink_ancestor_cannot_escape_output_root(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    output_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (output_root / "escape").symlink_to(outside, target_is_directory=True)

    plan = BuildPlan(
        pages=[
            PageBuildEntry(
                Route("/escape", Page("Escape")),
                PurePosixPath("escape/index.html"),
                "unsafe",
            )
        ]
    )

    with pytest.raises(OutputSymlinkError):
        FilesystemWriter().write(plan, output_root)

    assert list(outside.iterdir()) == []


def test_target_symlink_cannot_be_overwritten(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    output_root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("protected", encoding="utf-8")
    (output_root / "index.html").symlink_to(outside)

    plan = BuildPlan(
        pages=[
            PageBuildEntry(
                Route("/", Page("Home")),
                PurePosixPath("index.html"),
                "attacker-controlled replacement",
            )
        ]
    )

    with pytest.raises(OutputSymlinkError):
        FilesystemWriter().write(plan, output_root, overwrite=True)

    assert outside.read_text(encoding="utf-8") == "protected"


def test_asset_source_cannot_be_overwritten_before_copy(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    output_root.mkdir()
    source = output_root / "index.html"
    source.write_text("original asset", encoding="utf-8")

    plan = BuildPlan(
        pages=[
            PageBuildEntry(
                Route("/", Page("Home")),
                PurePosixPath("index.html"),
                "generated page",
            )
        ],
        assets=[
            AssetBuildEntry(
                Asset(
                    source,
                    PurePosixPath("assets/archive.html"),
                )
            )
        ],
    )

    with pytest.raises(AssetSourceOutputConflictError):
        FilesystemWriter().write(plan, output_root, overwrite=True)

    assert source.read_text(encoding="utf-8") == "original asset"
    assert not (output_root / "assets" / "archive.html").exists()


def test_symlinked_output_root_ancestor_cannot_redirect_build(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    linked_parent = tmp_path / "linked"
    linked_parent.symlink_to(outside, target_is_directory=True)
    output_root = linked_parent / "dist"

    plan = BuildPlan(
        pages=[
            PageBuildEntry(
                Route("/", Page("Home")),
                PurePosixPath("index.html"),
                "safe",
            )
        ]
    )

    with pytest.raises(OutputSymlinkError, match="traverse a symlink"):
        FilesystemWriter().write(plan, output_root)

    assert list(outside.iterdir()) == []


def test_overwrite_rejects_hardlinked_output_target(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    output_root.mkdir()
    outside = tmp_path / "outside.html"
    outside.write_text("protected", encoding="utf-8")
    (output_root / "index.html").hardlink_to(outside)

    plan = BuildPlan(
        pages=[
            PageBuildEntry(
                Route("/", Page("Home")),
                PurePosixPath("index.html"),
                "replacement",
            )
        ]
    )

    with pytest.raises(OutputPathConflictError, match="hard-linked"):
        FilesystemWriter().write(plan, output_root, overwrite=True)

    assert outside.read_text(encoding="utf-8") == "protected"


def test_asset_source_hardlink_to_output_is_rejected(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    output_root.mkdir()
    source = tmp_path / "source.bin"
    source.write_bytes(b"protected")
    destination = output_root / "asset.bin"
    destination.hardlink_to(source)

    plan = BuildPlan(
        assets=[
            AssetBuildEntry(
                Asset(
                    source,
                    PurePosixPath("asset.bin"),
                )
            )
        ]
    )

    with pytest.raises(AssetSourceOutputConflictError, match="shares an inode"):
        FilesystemWriter().write(plan, output_root, overwrite=True)

    assert source.read_bytes() == b"protected"
