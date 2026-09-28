from dataclasses import FrozenInstanceError
from pathlib import Path, PurePosixPath

import pytest

import pypagekit.development.watch as watch_module
from pypagekit.development import (
    DevelopmentWatcher,
    InvalidWatchRootError,
    WatchChange,
    WatchChangeBatch,
    WatchChangeKind,
    WatchPathKind,
    WatchSnapshot,
    WatchSnapshotEntry,
    WatchSnapshotError,
    diff_watch_snapshots,
)


def _entry(
    path: str,
    content: bytes,
    *,
    kind: WatchPathKind = WatchPathKind.FILE,
) -> WatchSnapshotEntry:
    import hashlib

    return WatchSnapshotEntry(
        PurePosixPath(path),
        kind,
        hashlib.sha256(content).hexdigest(),
    )


def test_watcher_constructor_does_not_scan_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "project"
    root.mkdir()

    def fail_scandir(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AssertionError("constructor must not scan")

    monkeypatch.setattr(watch_module.os, "scandir", fail_scandir)

    watcher = DevelopmentWatcher(root)

    assert watcher.root == root.resolve()
    assert watcher.ignored_paths == ()


def test_snapshot_is_lexically_deterministic_and_content_based(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "z.txt").write_text("z", encoding="utf-8")
    nested = root / "a"
    nested.mkdir()
    (nested / "b.txt").write_text("b", encoding="utf-8")
    (root / "m.txt").write_text("m", encoding="utf-8")

    snapshot = DevelopmentWatcher(root).snapshot()

    assert snapshot.paths == (
        PurePosixPath("a/b.txt"),
        PurePosixPath("m.txt"),
        PurePosixPath("z.txt"),
    )
    assert tuple(entry.kind for entry in snapshot) == (
        WatchPathKind.FILE,
        WatchPathKind.FILE,
        WatchPathKind.FILE,
    )


def test_snapshot_detects_same_size_content_change(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    target = root / "module.py"
    target.write_text("aaaa", encoding="utf-8")

    watcher = DevelopmentWatcher(root)
    before = watcher.snapshot()

    target.write_text("bbbb", encoding="utf-8")
    after = watcher.snapshot()

    batch = diff_watch_snapshots(before, after)

    assert batch.modified[0].path == PurePosixPath("module.py")
    assert batch.modified[0].before is not None
    assert batch.modified[0].after is not None
    assert (
        batch.modified[0].before.fingerprint
        != batch.modified[0].after.fingerprint
    )


def test_snapshot_records_symlink_target_without_following_it(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside-before", encoding="utf-8")
    link = root / "link.txt"
    link.symlink_to(outside)

    watcher = DevelopmentWatcher(root)
    before = watcher.snapshot()

    outside.write_text("outside-after", encoding="utf-8")
    after_outside_change = watcher.snapshot()

    assert before == after_outside_change
    entry = before.get(PurePosixPath("link.txt"))
    assert entry is not None
    assert entry.kind is WatchPathKind.SYMLINK

    replacement = tmp_path / "other.txt"
    replacement.write_text("other", encoding="utf-8")
    link.unlink()
    link.symlink_to(replacement)

    after_link_change = watcher.snapshot()
    batch = diff_watch_snapshots(before, after_link_change)

    assert batch.modified[0].path == PurePosixPath("link.txt")


def test_snapshot_ignores_empty_directories(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "empty").mkdir()

    assert DevelopmentWatcher(root).snapshot().entries == ()


def test_ignored_path_prefix_excludes_complete_subtree(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "site.py").write_text("print('site')", encoding="utf-8")
    ignored = root / "dist" / "assets"
    ignored.mkdir(parents=True)
    (ignored / "app.css").write_text("body{}", encoding="utf-8")

    watcher = DevelopmentWatcher(
        root,
        ignored_paths=[PurePosixPath("dist")],
    )

    assert watcher.ignored_paths == (PurePosixPath("dist"),)
    assert watcher.snapshot().paths == (PurePosixPath("site.py"),)


def test_nested_ignored_paths_are_reduced_to_outer_prefix(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()

    watcher = DevelopmentWatcher(
        root,
        ignored_paths=[
            PurePosixPath("dist/assets"),
            PurePosixPath("dist"),
            PurePosixPath("cache"),
        ],
    )

    assert watcher.ignored_paths == (
        PurePosixPath("cache"),
        PurePosixPath("dist"),
    )


def test_diff_classifies_created_modified_and_deleted_in_lexical_order(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    previous = WatchSnapshot(
        root,
        [
            _entry("b.txt", b"before"),
            _entry("d.txt", b"deleted"),
        ],
    )
    current = WatchSnapshot(
        root,
        [
            _entry("a.txt", b"created"),
            _entry("b.txt", b"after"),
            _entry("c.txt", b"created-too"),
        ],
    )

    batch = diff_watch_snapshots(previous, current)

    assert tuple(change.path for change in batch.changes) == (
        PurePosixPath("a.txt"),
        PurePosixPath("b.txt"),
        PurePosixPath("c.txt"),
        PurePosixPath("d.txt"),
    )
    assert tuple(change.kind for change in batch.changes) == (
        WatchChangeKind.CREATED,
        WatchChangeKind.MODIFIED,
        WatchChangeKind.CREATED,
        WatchChangeKind.DELETED,
    )
    assert tuple(change.path for change in batch.created) == (
        PurePosixPath("a.txt"),
        PurePosixPath("c.txt"),
    )
    assert tuple(change.path for change in batch.modified) == (
        PurePosixPath("b.txt"),
    )
    assert tuple(change.path for change in batch.deleted) == (
        PurePosixPath("d.txt"),
    )
    assert batch.has_changes is True


def test_kind_change_is_modified_even_with_same_fingerprint(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    fingerprint = _entry("value", b"same").fingerprint
    previous = WatchSnapshot(
        root,
        [
            WatchSnapshotEntry(
                PurePosixPath("value"),
                WatchPathKind.FILE,
                fingerprint,
            )
        ],
    )
    current = WatchSnapshot(
        root,
        [
            WatchSnapshotEntry(
                PurePosixPath("value"),
                WatchPathKind.SYMLINK,
                fingerprint,
            )
        ],
    )

    batch = diff_watch_snapshots(previous, current)

    assert tuple(change.kind for change in batch.changes) == (
        WatchChangeKind.MODIFIED,
    )


def test_poll_scans_once_and_returns_change_batch(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    target = root / "site.py"
    target.write_text("before", encoding="utf-8")
    watcher = DevelopmentWatcher(root)
    previous = watcher.snapshot()

    target.write_text("after", encoding="utf-8")
    batch = watcher.poll(previous)

    assert batch.current == watcher.snapshot()
    assert batch.modified[0].path == PurePosixPath("site.py")


def test_wait_for_changes_batches_until_snapshot_settles(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path.resolve()
    previous = WatchSnapshot(root, [_entry("a.txt", b"before")])
    first = WatchSnapshot(
        root,
        [
            _entry("a.txt", b"after"),
            _entry("b.txt", b"created"),
        ],
    )
    settled = WatchSnapshot(
        root,
        [
            _entry("a.txt", b"after"),
            _entry("b.txt", b"settled"),
        ],
    )
    snapshots = iter([first, settled, settled])
    watcher = DevelopmentWatcher(tmp_path)

    monkeypatch.setattr(watcher, "snapshot", lambda: next(snapshots))

    clock = [0.0]

    def monotonic() -> float:
        return clock[0]

    def sleep(seconds: float) -> None:
        clock[0] += seconds

    monkeypatch.setattr(watch_module.time, "monotonic", monotonic)
    monkeypatch.setattr(watch_module.time, "sleep", sleep)

    batch = watcher.wait_for_changes(
        previous,
        poll_interval=0.1,
        debounce_interval=0.1,
        timeout=1.0,
    )

    assert batch is not None
    assert batch.current == settled
    assert tuple(change.path for change in batch.changes) == (
        PurePosixPath("a.txt"),
        PurePosixPath("b.txt"),
    )


def test_wait_for_changes_returns_none_after_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    watcher = DevelopmentWatcher(tmp_path)
    previous = watcher.snapshot()
    clock = [0.0]

    monkeypatch.setattr(watcher, "snapshot", lambda: previous)
    monkeypatch.setattr(watch_module.time, "monotonic", lambda: clock[0])

    def sleep(seconds: float) -> None:
        clock[0] += seconds

    monkeypatch.setattr(watch_module.time, "sleep", sleep)

    assert (
        watcher.wait_for_changes(
            previous,
            poll_interval=0.1,
            debounce_interval=0.05,
            timeout=0.2,
        )
        is None
    )


def test_wait_for_changes_zero_debounce_returns_first_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path.resolve()
    previous = WatchSnapshot(root)
    current = WatchSnapshot(root, [_entry("new.txt", b"new")])
    watcher = DevelopmentWatcher(tmp_path)

    monkeypatch.setattr(watcher, "snapshot", lambda: current)

    batch = watcher.wait_for_changes(
        previous,
        debounce_interval=0,
        timeout=1.0,
    )

    assert batch is not None
    assert batch.current == current


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("poll_interval", 0),
        ("poll_interval", -0.1),
        ("debounce_interval", -0.1),
        ("timeout", -0.1),
    ],
)
def test_wait_for_changes_rejects_invalid_intervals(
    tmp_path: Path,
    name: str,
    value: float,
) -> None:
    watcher = DevelopmentWatcher(tmp_path)
    previous = watcher.snapshot()
    kwargs: dict[str, float] = {name: value}

    with pytest.raises(ValueError):
        watcher.wait_for_changes(previous, **kwargs)


def test_invalid_watch_roots_fail_explicitly(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    with pytest.raises(InvalidWatchRootError, match="does not exist"):
        DevelopmentWatcher(missing)

    file_root = tmp_path / "file"
    file_root.write_text("file", encoding="utf-8")
    with pytest.raises(InvalidWatchRootError, match="directory"):
        DevelopmentWatcher(file_root)

    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "linked"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(InvalidWatchRootError, match="symlink"):
        DevelopmentWatcher(link)


def test_snapshot_failure_when_root_disappears(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    watcher = DevelopmentWatcher(root)
    root.rmdir()

    with pytest.raises(WatchSnapshotError, match="no longer exists"):
        watcher.snapshot()


def test_snapshot_models_are_immutable(tmp_path: Path) -> None:
    entry = _entry("file.txt", b"content")
    snapshot = WatchSnapshot(tmp_path, [entry])
    change = WatchChange(
        PurePosixPath("file.txt"),
        WatchChangeKind.CREATED,
        None,
        entry,
    )
    batch = WatchChangeBatch(WatchSnapshot(tmp_path), snapshot, (change,))

    with pytest.raises(FrozenInstanceError):
        entry.fingerprint = "0" * 64  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        snapshot.root = tmp_path / "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        change.kind = WatchChangeKind.DELETED  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        batch.changes = ()  # type: ignore[misc]


def test_snapshot_and_change_validation() -> None:
    fingerprint = "0" * 64

    with pytest.raises(ValueError, match="relative"):
        WatchSnapshotEntry(
            PurePosixPath("/absolute"),
            WatchPathKind.FILE,
            fingerprint,
        )

    with pytest.raises(ValueError, match="64 lowercase"):
        WatchSnapshotEntry(
            PurePosixPath("file.txt"),
            WatchPathKind.FILE,
            "invalid",
        )

    with pytest.raises(ValueError, match="only an after"):
        WatchChange(
            PurePosixPath("file.txt"),
            WatchChangeKind.CREATED,
            _entry("file.txt", b"before"),
            _entry("file.txt", b"after"),
        )


def test_diff_rejects_different_roots(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="same root"):
        diff_watch_snapshots(
            WatchSnapshot(tmp_path / "a"),
            WatchSnapshot(tmp_path / "b"),
        )
