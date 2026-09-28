from dataclasses import FrozenInstanceError
from pathlib import Path, PurePosixPath

import pytest

import pypagekit._filesystem_transaction as transaction_module
import pypagekit.build.filesystem as filesystem_module

from pypagekit import Asset, Page, Route
from pypagekit.build import (
    AssetBuildEntry,
    BuildPlan,
    FilesystemWriteResult,
    FilesystemWriter,
    IncrementalFilesystemWriteResult,
    PageBuildEntry,
    build_manifest,
)
from pypagekit.exceptions import (
    AssetSourceOutputConflictError,
    ExistingOutputError,
    FilesystemRollbackError,
    FilesystemWriteError,
    InvalidAssetSourceForOutputError,
    IncrementalOutputDriftError,
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



def test_write_failure_rolls_back_prior_new_files_and_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"source")
    output_root = tmp_path / "dist"
    plan = BuildPlan(
        pages=[page_entry("docs/index.html", "generated")],
        assets=[asset_entry(source, "assets/source.bin")],
    )

    def fail_copy(*args: object, **kwargs: object) -> None:
        raise OSError("simulated copy failure")

    monkeypatch.setattr(filesystem_module.shutil, "copyfileobj", fail_copy)

    with pytest.raises(FilesystemWriteError, match="Filesystem output failed"):
        FilesystemWriter().write(plan, output_root)

    assert not output_root.exists()


def test_overwrite_failure_restores_existing_files_and_removes_new_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_root = tmp_path / "dist"
    output_root.mkdir()
    page = output_root / "index.html"
    page.write_text("old page", encoding="utf-8")
    unrelated = output_root / "keep.txt"
    unrelated.write_text("keep", encoding="utf-8")
    source = tmp_path / "source.bin"
    source.write_bytes(b"source")
    plan = BuildPlan(
        pages=[
            page_entry("index.html", "new page"),
            page_entry("docs/new.html", "new nested page"),
        ],
        assets=[asset_entry(source, "assets/source.bin")],
    )

    def fail_copy(*args: object, **kwargs: object) -> None:
        raise OSError("simulated copy failure")

    monkeypatch.setattr(filesystem_module.shutil, "copyfileobj", fail_copy)

    with pytest.raises(FilesystemWriteError):
        FilesystemWriter().write(plan, output_root, overwrite=True)

    assert page.read_text(encoding="utf-8") == "old page"
    assert unrelated.read_text(encoding="utf-8") == "keep"
    assert not (output_root / "docs").exists()
    assert not (output_root / "assets").exists()
    assert not tuple(output_root.glob(".pypagekit-backup-*"))


def test_partial_asset_copy_is_removed_during_rollback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"source")
    output_root = tmp_path / "dist"

    def partial_copy(source_file: object, output_file: object) -> None:
        del source_file
        output_file.write(b"partial")  # type: ignore[attr-defined]
        raise OSError("copy interrupted")

    monkeypatch.setattr(filesystem_module.shutil, "copyfileobj", partial_copy)

    with pytest.raises(FilesystemWriteError):
        FilesystemWriter().write(
            BuildPlan(assets=[asset_entry(source, "assets/source.bin")]),
            output_root,
        )

    assert not output_root.exists()


def test_rollback_failure_is_reported_explicitly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_root = tmp_path / "dist"
    output_root.mkdir()
    page = output_root / "index.html"
    page.write_text("old page", encoding="utf-8")
    source = tmp_path / "source.bin"
    source.write_bytes(b"source")
    plan = BuildPlan(
        pages=[page_entry("index.html", "new page")],
        assets=[asset_entry(source, "assets/source.bin")],
    )

    def fail_copy(*args: object, **kwargs: object) -> None:
        raise OSError("simulated copy failure")

    def fail_restore(source_path: object, destination_path: object) -> None:
        del source_path, destination_path
        raise OSError("simulated rollback failure")

    monkeypatch.setattr(filesystem_module.shutil, "copyfileobj", fail_copy)
    monkeypatch.setattr(transaction_module.os, "replace", fail_restore)

    with pytest.raises(FilesystemRollbackError, match="rollback failed"):
        FilesystemWriter().write(plan, output_root, overwrite=True)


def test_incremental_writer_classifies_and_applies_minimal_mutations(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "dist"
    old_asset_source = tmp_path / "old.css"
    old_asset_source.write_text("old css", encoding="utf-8")
    initial_plan = BuildPlan(
        pages=[
            page_entry("index.html", "same"),
            page_entry("changed.html", "before"),
            page_entry("removed.html", "remove me"),
        ],
        assets=[
            asset_entry(old_asset_source, "assets/app.css"),
        ],
    )
    previous_manifest = build_manifest(initial_plan)
    FilesystemWriter().write(initial_plan, output_root)

    new_asset_source = tmp_path / "new.css"
    new_asset_source.write_text("new css", encoding="utf-8")
    next_plan = BuildPlan(
        pages=[
            page_entry("index.html", "same"),
            page_entry("changed.html", "after"),
            page_entry("added.html", "new page"),
        ],
        assets=[
            asset_entry(new_asset_source, "assets/app.css"),
        ],
    )

    result = FilesystemWriter().write_incremental(
        next_plan,
        previous_manifest,
        output_root,
    )

    assert isinstance(result, IncrementalFilesystemWriteResult)
    assert result.diff.added_targets == (PurePosixPath("added.html"),)
    assert result.diff.changed_targets == (
        PurePosixPath("changed.html"),
        PurePosixPath("assets/app.css"),
    )
    assert result.diff.unchanged_targets == (PurePosixPath("index.html"),)
    assert result.diff.removed_targets == (PurePosixPath("removed.html"),)
    assert result.added_files == (output_root / "added.html",)
    assert result.changed_files == (
        output_root / "changed.html",
        output_root / "assets" / "app.css",
    )
    assert result.removed_files == (output_root / "removed.html",)
    assert result.unchanged_files == (output_root / "index.html",)
    assert result.written_files == (
        output_root / "changed.html",
        output_root / "added.html",
        output_root / "assets" / "app.css",
    )
    assert result.files == (
        output_root / "index.html",
        output_root / "changed.html",
        output_root / "added.html",
        output_root / "assets" / "app.css",
    )

    assert (output_root / "index.html").read_text(encoding="utf-8") == "same"
    assert (output_root / "changed.html").read_text(encoding="utf-8") == "after"
    assert (output_root / "added.html").read_text(encoding="utf-8") == "new page"
    assert (output_root / "assets" / "app.css").read_text(encoding="utf-8") == "new css"
    assert not (output_root / "removed.html").exists()


def test_incremental_writer_no_change_performs_no_transactional_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_root = tmp_path / "dist"
    plan = BuildPlan(
        pages=[page_entry("index.html", "same")],
    )
    previous_manifest = build_manifest(plan)
    FilesystemWriter().write(plan, output_root)

    def fail_prepare(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("no mutation should be prepared")

    monkeypatch.setattr(
        transaction_module.FilesystemTransaction,
        "prepare_file",
        fail_prepare,
    )

    result = FilesystemWriter().write_incremental(
        plan,
        previous_manifest,
        output_root,
    )

    assert result.diff.has_changes is False
    assert result.written_files == ()
    assert result.removed_files == ()
    assert result.unchanged_files == (output_root / "index.html",)


def test_incremental_writer_preserves_unplanned_existing_files(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    initial_plan = BuildPlan(
        pages=[page_entry("index.html", "before")],
    )
    previous_manifest = build_manifest(initial_plan)
    FilesystemWriter().write(initial_plan, output_root)
    unplanned = output_root / "keep.txt"
    unplanned.write_text("keep", encoding="utf-8")

    FilesystemWriter().write_incremental(
        BuildPlan(pages=[page_entry("index.html", "after")]),
        previous_manifest,
        output_root,
    )

    assert unplanned.read_text(encoding="utf-8") == "keep"


def test_incremental_writer_rejects_modified_tracked_output(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    plan = BuildPlan(
        pages=[page_entry("index.html", "generated")],
    )
    previous_manifest = build_manifest(plan)
    FilesystemWriter().write(plan, output_root)
    target = output_root / "index.html"
    target.write_text("manual edit", encoding="utf-8")

    with pytest.raises(IncrementalOutputDriftError, match="no longer matches"):
        FilesystemWriter().write_incremental(
            plan,
            previous_manifest,
            output_root,
        )

    assert target.read_text(encoding="utf-8") == "manual edit"


def test_incremental_writer_rejects_missing_tracked_output(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    plan = BuildPlan(
        pages=[page_entry("index.html", "generated")],
    )
    previous_manifest = build_manifest(plan)
    FilesystemWriter().write(plan, output_root)
    (output_root / "index.html").unlink()

    with pytest.raises(IncrementalOutputDriftError, match="missing"):
        FilesystemWriter().write_incremental(
            plan,
            previous_manifest,
            output_root,
        )


def test_incremental_writer_rejects_missing_tracked_output_root(tmp_path: Path) -> None:
    plan = BuildPlan(
        pages=[page_entry("index.html", "generated")],
    )
    previous_manifest = build_manifest(plan)

    with pytest.raises(IncrementalOutputDriftError, match="root"):
        FilesystemWriter().write_incremental(
            plan,
            previous_manifest,
            tmp_path / "dist",
        )


def test_incremental_writer_rejects_hard_linked_tracked_output(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    plan = BuildPlan(
        pages=[page_entry("index.html", "generated")],
    )
    previous_manifest = build_manifest(plan)
    FilesystemWriter().write(plan, output_root)
    alias = tmp_path / "alias.html"
    alias.hardlink_to(output_root / "index.html")

    with pytest.raises(OutputPathConflictError, match="hard-linked"):
        FilesystemWriter().write_incremental(
            plan,
            previous_manifest,
            output_root,
        )


def test_incremental_writer_rejects_symlinked_tracked_output(tmp_path: Path) -> None:
    output_root = tmp_path / "dist"
    output_root.mkdir()
    outside = tmp_path / "outside.html"
    outside.write_text("generated", encoding="utf-8")
    tracked = output_root / "index.html"
    tracked.symlink_to(outside)
    previous_manifest = build_manifest(
        BuildPlan(pages=[page_entry("index.html", "generated")])
    )

    with pytest.raises(OutputSymlinkError, match="target"):
        FilesystemWriter().write_incremental(
            BuildPlan(pages=[page_entry("index.html", "generated")]),
            previous_manifest,
            output_root,
        )


def test_incremental_failure_restores_removed_and_changed_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_root = tmp_path / "dist"
    source = tmp_path / "asset.bin"
    source.write_bytes(b"before")
    initial_plan = BuildPlan(
        pages=[
            page_entry("changed.html", "before"),
            page_entry("removed.html", "remove me"),
        ],
        assets=[asset_entry(source, "assets/asset.bin")],
    )
    previous_manifest = build_manifest(initial_plan)
    FilesystemWriter().write(initial_plan, output_root)

    source.write_bytes(b"after")
    next_plan = BuildPlan(
        pages=[page_entry("changed.html", "after")],
        assets=[asset_entry(source, "assets/asset.bin")],
    )

    def fail_copy(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise OSError("simulated incremental copy failure")

    monkeypatch.setattr(filesystem_module.shutil, "copyfileobj", fail_copy)

    with pytest.raises(FilesystemWriteError):
        FilesystemWriter().write_incremental(
            next_plan,
            previous_manifest,
            output_root,
        )

    assert (output_root / "changed.html").read_text(encoding="utf-8") == "before"
    assert (output_root / "removed.html").read_text(encoding="utf-8") == "remove me"
    assert (output_root / "assets" / "asset.bin").read_bytes() == b"before"
    assert not tuple(output_root.rglob(".pypagekit-backup-*"))


def test_incremental_writer_rolls_back_when_written_bytes_miss_planned_fingerprint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_root = tmp_path / "dist"
    source = tmp_path / "asset.bin"
    source.write_bytes(b"before")
    initial_plan = BuildPlan(
        assets=[asset_entry(source, "assets/asset.bin")],
    )
    previous_manifest = build_manifest(initial_plan)
    FilesystemWriter().write(initial_plan, output_root)

    source.write_bytes(b"after")
    next_plan = BuildPlan(
        assets=[asset_entry(source, "assets/asset.bin")],
    )

    def corrupt_copy(source_file: object, output_file: object) -> None:
        del source_file
        output_file.write(b"corrupt")  # type: ignore[attr-defined]

    monkeypatch.setattr(filesystem_module.shutil, "copyfileobj", corrupt_copy)

    with pytest.raises(FilesystemWriteError, match="Filesystem output failed"):
        FilesystemWriter().write_incremental(
            next_plan,
            previous_manifest,
            output_root,
        )

    assert (output_root / "assets" / "asset.bin").read_bytes() == b"before"


def test_incremental_writer_rejects_asset_source_that_is_removed_output(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "dist"
    initial_plan = BuildPlan(
        pages=[page_entry("source.txt", "source bytes")],
    )
    previous_manifest = build_manifest(initial_plan)
    FilesystemWriter().write(initial_plan, output_root)

    next_plan = BuildPlan(
        assets=[
            asset_entry(
                output_root / "source.txt",
                "assets/copied.txt",
            )
        ]
    )

    with pytest.raises(AssetSourceOutputConflictError):
        FilesystemWriter().write_incremental(
            next_plan,
            previous_manifest,
            output_root,
        )

    assert (output_root / "source.txt").read_text(encoding="utf-8") == "source bytes"
    assert not (output_root / "assets").exists()


def test_incremental_writer_validates_arguments(tmp_path: Path) -> None:
    writer = FilesystemWriter()
    manifest = build_manifest(BuildPlan())

    with pytest.raises(TypeError, match="BuildPlan"):
        writer.write_incremental(
            object(),  # type: ignore[arg-type]
            manifest,
            tmp_path / "dist",
        )

    with pytest.raises(TypeError, match="previous_manifest"):
        writer.write_incremental(
            BuildPlan(),
            object(),  # type: ignore[arg-type]
            tmp_path / "dist",
        )

    with pytest.raises(TypeError, match="pathlib.Path"):
        writer.write_incremental(
            BuildPlan(),
            manifest,
            "dist",  # type: ignore[arg-type]
        )


def test_incremental_write_result_is_immutable(tmp_path: Path) -> None:
    manifest = build_manifest(BuildPlan())
    result = IncrementalFilesystemWriteResult(
        tmp_path,
        manifest,
        filesystem_module.diff_build_manifests(manifest, manifest),
        (),
        (),
        (),
        (),
    )

    with pytest.raises(FrozenInstanceError):
        result.output_root = tmp_path / "other"  # type: ignore[misc]
