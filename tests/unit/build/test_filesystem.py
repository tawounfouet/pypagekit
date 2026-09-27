from dataclasses import FrozenInstanceError
from pathlib import Path, PurePosixPath

import pytest

import pypagekit.build.filesystem as filesystem_module

from pypagekit import Asset, Page, Route
from pypagekit.build import (
    AssetBuildEntry,
    BuildPlan,
    FilesystemWriteResult,
    FilesystemWriter,
    PageBuildEntry,
)
from pypagekit.exceptions import (
    AssetSourceOutputConflictError,
    ExistingOutputError,
    FilesystemWriteError,
    InvalidAssetSourceForOutputError,
    InvalidOutputRootError,
    OutputPathConflictError,
    OutputSymlinkError,
)


def page_entry(target: str, content: str = "<html></html>") -> PageBuildEntry:
    return PageBuildEntry(
        Route("/", Page("Home")),
        PurePosixPath(target),
        content,
    )


def asset_entry(source: Path, target: str) -> AssetBuildEntry:
    return AssetBuildEntry(Asset(source, PurePosixPath(target)))


def test_empty_plan_creates_output_root(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"

    result = FilesystemWriter().write(BuildPlan(), output_root)

    assert output_root.is_dir()
    assert result == FilesystemWriteResult(output_root, (), ())
    assert result.files == ()


def test_writer_writes_page_content_as_utf8(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    plan = BuildPlan(
        pages=[
            page_entry(
                "docs/index.html",
                "<p>Café — données</p>",
            )
        ]
    )

    result = FilesystemWriter().write(plan, output_root)

    destination = output_root / "docs" / "index.html"
    assert destination.read_text(encoding="utf-8") == "<p>Café — données</p>"
    assert result.page_files == (destination,)
    assert result.asset_files == ()
    assert result.files == (destination,)


def test_writer_copies_asset_bytes(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"\x00\x01asset")
    output_root = tmp_path / "dist"
    plan = BuildPlan(assets=[asset_entry(source, "assets/source.bin")])

    result = FilesystemWriter().write(plan, output_root)

    destination = output_root / "assets" / "source.bin"
    assert destination.read_bytes() == b"\x00\x01asset"
    assert result.asset_files == (destination,)


def test_writer_preserves_unplanned_existing_files(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    output_root.mkdir()
    unplanned = output_root / "keep.txt"
    unplanned.write_text("keep", encoding="utf-8")

    FilesystemWriter().write(
        BuildPlan(pages=[page_entry("index.html")]),
        output_root,
    )

    assert unplanned.read_text(encoding="utf-8") == "keep"


def test_existing_target_is_rejected_by_default(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    output_root.mkdir()
    target = output_root / "index.html"
    target.write_text("existing", encoding="utf-8")

    with pytest.raises(ExistingOutputError, match="already exists"):
        FilesystemWriter().write(
            BuildPlan(pages=[page_entry("index.html", "new")]),
            output_root,
        )

    assert target.read_text(encoding="utf-8") == "existing"


def test_overwrite_true_replaces_existing_page(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    output_root.mkdir()
    target = output_root / "index.html"
    target.write_text("old", encoding="utf-8")

    FilesystemWriter().write(
        BuildPlan(pages=[page_entry("index.html", "new")]),
        output_root,
        overwrite=True,
    )

    assert target.read_text(encoding="utf-8") == "new"


def test_overwrite_true_replaces_existing_asset(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("new", encoding="utf-8")
    output_root = tmp_path / "dist"
    target = output_root / "assets" / "source.txt"
    target.parent.mkdir(parents=True)
    target.write_text("old", encoding="utf-8")

    FilesystemWriter().write(
        BuildPlan(assets=[asset_entry(source, "assets/source.txt")]),
        output_root,
        overwrite=True,
    )

    assert target.read_text(encoding="utf-8") == "new"


def test_preflight_rejects_existing_target_before_any_write(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    output_root.mkdir()
    existing = output_root / "second.html"
    existing.write_text("existing", encoding="utf-8")
    first = output_root / "first.html"
    plan = BuildPlan(
        pages=[
            page_entry("first.html", "first"),
            page_entry("second.html", "second"),
        ]
    )

    with pytest.raises(ExistingOutputError):
        FilesystemWriter().write(plan, output_root)

    assert not first.exists()
    assert existing.read_text(encoding="utf-8") == "existing"


def test_missing_asset_source_fails_before_output_root_creation(tmp_path: Path) -> None:
    source = tmp_path / "missing.txt"
    output_root = tmp_path / "dist"
    plan = BuildPlan(assets=[asset_entry(source, "assets/missing.txt")])

    with pytest.raises(InvalidAssetSourceForOutputError, match="does not exist"):
        FilesystemWriter().write(plan, output_root)

    assert not output_root.exists()


def test_broken_asset_source_symlink_fails_before_output_creation(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.txt"
    source = tmp_path / "broken.txt"
    source.symlink_to(missing)
    output_root = tmp_path / "dist"

    with pytest.raises(InvalidAssetSourceForOutputError, match="broken symlink"):
        FilesystemWriter().write(
            BuildPlan(assets=[asset_entry(source, "assets/broken.txt")]),
            output_root,
        )

    assert not output_root.exists()


def test_asset_source_must_be_regular_file(tmp_path: Path) -> None:
    source = tmp_path / "source-dir"
    source.mkdir()

    with pytest.raises(InvalidAssetSourceForOutputError, match="regular file"):
        FilesystemWriter().write(
            BuildPlan(assets=[asset_entry(source, "assets/source")]),
            tmp_path / "dist",
        )


def test_output_root_cannot_be_existing_file(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    output_root.write_text("file", encoding="utf-8")

    with pytest.raises(InvalidOutputRootError, match="directory"):
        FilesystemWriter().write(BuildPlan(), output_root)


def test_existing_directory_at_file_target_is_rejected(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    target = output_root / "docs" / "index.html"
    target.mkdir(parents=True)

    with pytest.raises(OutputPathConflictError, match="existing directory"):
        FilesystemWriter().write(
            BuildPlan(pages=[page_entry("docs/index.html")]),
            output_root,
        )


def test_existing_file_in_target_ancestor_is_rejected(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    output_root.mkdir()
    ancestor = output_root / "docs"
    ancestor.write_text("file", encoding="utf-8")

    with pytest.raises(OutputPathConflictError, match="not a directory"):
        FilesystemWriter().write(
            BuildPlan(pages=[page_entry("docs/index.html")]),
            output_root,
        )


def test_asset_source_cannot_be_any_planned_output_destination(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "dist"
    output_root.mkdir()
    source = output_root / "index.html"
    source.write_text("source", encoding="utf-8")
    plan = BuildPlan(
        pages=[page_entry("index.html", "generated")],
        assets=[asset_entry(source, "assets/copy.html")],
    )

    with pytest.raises(AssetSourceOutputConflictError):
        FilesystemWriter().write(plan, output_root, overwrite=True)

    assert source.read_text(encoding="utf-8") == "source"


def test_writer_rejects_invalid_arguments(tmp_path: Path) -> None:
    writer = FilesystemWriter()

    with pytest.raises(TypeError, match="BuildPlan"):
        writer.write("invalid", tmp_path / "dist")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="pathlib.Path"):
        writer.write(BuildPlan(), "dist")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="bool"):
        writer.write(BuildPlan(), tmp_path / "dist", overwrite=1)  # type: ignore[arg-type]


def test_unexpected_io_failure_is_wrapped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"source")

    def fail_copy(*args: object, **kwargs: object) -> None:
        raise OSError("simulated copy failure")

    monkeypatch.setattr(filesystem_module.shutil, "copyfileobj", fail_copy)

    with pytest.raises(FilesystemWriteError, match="Filesystem output failed"):
        FilesystemWriter().write(
            BuildPlan(assets=[asset_entry(source, "assets/source.bin")]),
            tmp_path / "dist",
        )


def test_write_result_is_immutable(tmp_path: Path) -> None:
    result = FilesystemWriteResult(tmp_path, (), ())

    with pytest.raises(FrozenInstanceError):
        result.output_root = tmp_path / "other"  # type: ignore[misc]


def test_output_root_symlink_is_rejected(tmp_path: Path) -> None:
    real_root = tmp_path / "real"
    real_root.mkdir()
    output_root = tmp_path / "dist"
    output_root.symlink_to(real_root, target_is_directory=True)

    with pytest.raises(OutputSymlinkError, match="Output root"):
        FilesystemWriter().write(BuildPlan(), output_root)


def test_target_ancestor_symlink_is_rejected(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    output_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (output_root / "docs").symlink_to(outside, target_is_directory=True)

    with pytest.raises(OutputSymlinkError, match="ancestor"):
        FilesystemWriter().write(
            BuildPlan(pages=[page_entry("docs/index.html", "unsafe")]),
            output_root,
        )

    assert not (outside / "index.html").exists()


def test_target_symlink_is_rejected_even_with_overwrite(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    output_root.mkdir()
    outside = tmp_path / "outside.html"
    outside.write_text("outside", encoding="utf-8")
    (output_root / "index.html").symlink_to(outside)

    with pytest.raises(OutputSymlinkError, match="target"):
        FilesystemWriter().write(
            BuildPlan(pages=[page_entry("index.html", "unsafe")]),
            output_root,
            overwrite=True,
        )

    assert outside.read_text(encoding="utf-8") == "outside"
