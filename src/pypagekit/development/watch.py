"""Explicit deterministic filesystem watching for local development."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import time
from bisect import bisect_left
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path, PurePosixPath

from .exceptions import InvalidWatchRootError, WatchSnapshotError

_SHA256_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_READ_CHUNK_SIZE = 1024 * 1024


class WatchPathKind(StrEnum):
    """Filesystem path kinds represented in a development watch snapshot."""

    FILE = "file"
    SYMLINK = "symlink"


class WatchChangeKind(StrEnum):
    """Change classifications emitted between two watch snapshots."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass(frozen=True, slots=True)
class WatchSnapshotEntry:
    """Immutable content identity for one watched relative path."""

    path: PurePosixPath
    kind: WatchPathKind
    fingerprint: str

    def __post_init__(self) -> None:
        _validate_relative_path(self.path, label="Watch snapshot path")
        if not isinstance(self.kind, WatchPathKind):
            raise TypeError("Watch snapshot entry kind must be a WatchPathKind.")
        if not isinstance(self.fingerprint, str):
            raise TypeError("Watch snapshot entry fingerprint must be a string.")
        if _SHA256_DIGEST_RE.fullmatch(self.fingerprint) is None:
            raise ValueError(
                "Watch snapshot fingerprint must contain exactly "
                "64 lowercase hexadecimal characters."
            )


@dataclass(frozen=True, slots=True, init=False)
class WatchSnapshot:
    """Immutable deterministic snapshot of watched files and symlinks."""

    root: Path
    entries: tuple[WatchSnapshotEntry, ...]
    _lookup_paths: tuple[str, ...] = field(init=False, repr=False, compare=False)
    _lookup_entries: tuple[WatchSnapshotEntry, ...] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __init__(
        self,
        root: Path,
        entries: Iterable[WatchSnapshotEntry] = (),
    ) -> None:
        if not isinstance(root, Path):
            raise TypeError("Watch snapshot root must be a pathlib.Path.")

        try:
            normalized = tuple(entries)
        except TypeError as exc:
            raise TypeError("Watch snapshot entries must be an iterable.") from exc

        invalid = [entry for entry in normalized if not isinstance(entry, WatchSnapshotEntry)]
        if invalid:
            invalid_type = type(invalid[0]).__name__
            raise TypeError(
                f"Watch snapshot must contain only WatchSnapshotEntry objects; got {invalid_type}."
            )

        ordered = tuple(sorted(normalized, key=lambda entry: entry.path.as_posix()))
        paths = tuple(entry.path.as_posix() for entry in ordered)
        if len(paths) != len(set(paths)):
            raise ValueError("Watch snapshot paths must be unique.")

        object.__setattr__(self, "root", root)
        object.__setattr__(self, "entries", ordered)
        object.__setattr__(self, "_lookup_paths", paths)
        object.__setattr__(self, "_lookup_entries", ordered)

    @property
    def paths(self) -> tuple[PurePosixPath, ...]:
        """Return watched paths in deterministic lexical order."""

        return tuple(entry.path for entry in self.entries)

    def get(self, path: PurePosixPath) -> WatchSnapshotEntry | None:
        """Return the entry for one relative path, or None when absent."""

        _validate_relative_path(path, label="Watch snapshot lookup path")
        key = path.as_posix()
        index = bisect_left(self._lookup_paths, key)
        if index >= len(self._lookup_paths) or self._lookup_paths[index] != key:
            return None
        return self._lookup_entries[index]

    def __iter__(self) -> Iterator[WatchSnapshotEntry]:
        return iter(self.entries)

    def __len__(self) -> int:
        return len(self.entries)


@dataclass(frozen=True, slots=True)
class WatchChange:
    """One deterministic path-level change between watch snapshots."""

    path: PurePosixPath
    kind: WatchChangeKind
    before: WatchSnapshotEntry | None
    after: WatchSnapshotEntry | None

    def __post_init__(self) -> None:
        _validate_relative_path(self.path, label="Watch change path")
        if not isinstance(self.kind, WatchChangeKind):
            raise TypeError("Watch change kind must be a WatchChangeKind.")

        if self.kind is WatchChangeKind.CREATED:
            if self.before is not None or self.after is None:
                raise ValueError("Created watch changes require only an after entry.")
        elif self.kind is WatchChangeKind.MODIFIED:
            if self.before is None or self.after is None:
                raise ValueError("Modified watch changes require before and after entries.")
        else:
            if self.before is None or self.after is not None:
                raise ValueError("Deleted watch changes require only a before entry.")

        for entry in (self.before, self.after):
            if entry is not None and entry.path != self.path:
                raise ValueError("Watch change entry path must match the change path.")


@dataclass(frozen=True, slots=True)
class WatchChangeBatch:
    """Immutable change batch from one watch snapshot to another."""

    previous: WatchSnapshot
    current: WatchSnapshot
    changes: tuple[WatchChange, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.previous, WatchSnapshot):
            raise TypeError("Watch change batch previous value must be a WatchSnapshot.")
        if not isinstance(self.current, WatchSnapshot):
            raise TypeError("Watch change batch current value must be a WatchSnapshot.")
        if self.previous.root != self.current.root:
            raise ValueError("Watch change batch snapshots must have the same root.")
        if not isinstance(self.changes, tuple):
            raise TypeError("Watch change batch changes must be a tuple.")
        if any(not isinstance(change, WatchChange) for change in self.changes):
            raise TypeError("Watch change batch must contain only WatchChange objects.")

        paths = tuple(change.path for change in self.changes)
        if len(paths) != len(set(paths)):
            raise ValueError("Watch change batch paths must be unique.")

    @property
    def created(self) -> tuple[WatchChange, ...]:
        """Return created-path changes."""

        return tuple(change for change in self.changes if change.kind is WatchChangeKind.CREATED)

    @property
    def modified(self) -> tuple[WatchChange, ...]:
        """Return modified-path changes."""

        return tuple(change for change in self.changes if change.kind is WatchChangeKind.MODIFIED)

    @property
    def deleted(self) -> tuple[WatchChange, ...]:
        """Return deleted-path changes."""

        return tuple(change for change in self.changes if change.kind is WatchChangeKind.DELETED)

    @property
    def has_changes(self) -> bool:
        """Return whether this batch contains at least one path change."""

        return bool(self.changes)


def diff_watch_snapshots(
    previous: WatchSnapshot,
    current: WatchSnapshot,
) -> WatchChangeBatch:
    """Return a deterministic lexical diff between two watch snapshots."""

    if not isinstance(previous, WatchSnapshot):
        raise TypeError("Previous watch snapshot must be a WatchSnapshot.")
    if not isinstance(current, WatchSnapshot):
        raise TypeError("Current watch snapshot must be a WatchSnapshot.")
    if previous.root != current.root:
        raise ValueError("Watch snapshots must have the same root.")

    changes: list[WatchChange] = []
    previous_index = 0
    current_index = 0

    while previous_index < len(previous.entries) or current_index < len(current.entries):
        previous_entry = (
            previous.entries[previous_index] if previous_index < len(previous.entries) else None
        )
        current_entry = (
            current.entries[current_index] if current_index < len(current.entries) else None
        )

        if previous_entry is None:
            assert current_entry is not None
            changes.append(
                WatchChange(
                    current_entry.path,
                    WatchChangeKind.CREATED,
                    None,
                    current_entry,
                )
            )
            current_index += 1
            continue

        if current_entry is None:
            changes.append(
                WatchChange(
                    previous_entry.path,
                    WatchChangeKind.DELETED,
                    previous_entry,
                    None,
                )
            )
            previous_index += 1
            continue

        previous_key = previous_entry.path.as_posix()
        current_key = current_entry.path.as_posix()

        if previous_key < current_key:
            changes.append(
                WatchChange(
                    previous_entry.path,
                    WatchChangeKind.DELETED,
                    previous_entry,
                    None,
                )
            )
            previous_index += 1
        elif current_key < previous_key:
            changes.append(
                WatchChange(
                    current_entry.path,
                    WatchChangeKind.CREATED,
                    None,
                    current_entry,
                )
            )
            current_index += 1
        else:
            if (
                previous_entry.kind != current_entry.kind
                or previous_entry.fingerprint != current_entry.fingerprint
            ):
                changes.append(
                    WatchChange(
                        current_entry.path,
                        WatchChangeKind.MODIFIED,
                        previous_entry,
                        current_entry,
                    )
                )
            previous_index += 1
            current_index += 1

    return WatchChangeBatch(previous, current, tuple(changes))


class DevelopmentWatcher:
    """Explicit polling watcher with no background threads or import-time work."""

    def __init__(
        self,
        root: Path,
        *,
        ignored_paths: Iterable[PurePosixPath] = (),
    ) -> None:
        self._root = _validate_watch_root(root)
        self._ignored_paths = _normalize_ignored_paths(ignored_paths)

    @property
    def root(self) -> Path:
        """Return the normalized absolute watch root."""

        return self._root

    @property
    def ignored_paths(self) -> tuple[PurePosixPath, ...]:
        """Return ignored relative path prefixes."""

        return self._ignored_paths

    def snapshot(self) -> WatchSnapshot:
        """Read one deterministic snapshot of watched files and symlinks."""

        try:
            if not self._root.exists():
                raise WatchSnapshotError(f"Watch root '{self._root}' no longer exists.")
            if self._root.is_symlink() or not self._root.is_dir():
                raise WatchSnapshotError(
                    f"Watch root '{self._root}' is no longer a safe directory."
                )

            entries: list[WatchSnapshotEntry] = []
            self._scan_directory(self._root, PurePosixPath(), entries)
            return WatchSnapshot(self._root, entries)
        except WatchSnapshotError:
            raise
        except OSError as exc:
            raise WatchSnapshotError(
                f"Unable to read a deterministic watch snapshot under '{self._root}'."
            ) from exc

    def poll(self, previous: WatchSnapshot) -> WatchChangeBatch:
        """Take one snapshot and diff it against a previous snapshot."""

        if not isinstance(previous, WatchSnapshot):
            raise TypeError("Development watcher previous snapshot must be a WatchSnapshot.")
        if previous.root != self._root:
            raise ValueError("Previous watch snapshot root does not match this watcher.")

        return diff_watch_snapshots(previous, self.snapshot())

    def wait_for_changes(
        self,
        previous: WatchSnapshot,
        *,
        poll_interval: float = 0.1,
        debounce_interval: float = 0.05,
        timeout: float | None = None,
    ) -> WatchChangeBatch | None:
        """Block explicitly until a settled change batch is available or timeout expires."""

        if not isinstance(previous, WatchSnapshot):
            raise TypeError("Development watcher previous snapshot must be a WatchSnapshot.")
        if previous.root != self._root:
            raise ValueError("Previous watch snapshot root does not match this watcher.")

        poll_interval = _validate_interval(
            poll_interval,
            label="poll_interval",
            allow_zero=False,
        )
        debounce_interval = _validate_interval(
            debounce_interval,
            label="debounce_interval",
            allow_zero=True,
        )
        if timeout is not None:
            timeout = _validate_interval(timeout, label="timeout", allow_zero=True)

        started = time.monotonic()
        deadline = None if timeout is None else started + timeout

        while True:
            current = self.snapshot()
            if current != previous:
                candidate = current
                if debounce_interval == 0:
                    return diff_watch_snapshots(previous, candidate)

                last_change = time.monotonic()
                while True:
                    now = time.monotonic()
                    if deadline is not None and now >= deadline:
                        return diff_watch_snapshots(previous, candidate)

                    sleep_for = min(poll_interval, debounce_interval)
                    if deadline is not None:
                        sleep_for = min(sleep_for, max(0.0, deadline - now))
                    if sleep_for > 0:
                        time.sleep(sleep_for)

                    next_snapshot = self.snapshot()
                    now = time.monotonic()
                    if next_snapshot != candidate:
                        candidate = next_snapshot
                        last_change = now

                    if now - last_change >= debounce_interval:
                        return diff_watch_snapshots(previous, candidate)

            now = time.monotonic()
            if deadline is not None and now >= deadline:
                return None

            sleep_for = poll_interval
            if deadline is not None:
                sleep_for = min(sleep_for, max(0.0, deadline - now))
            if sleep_for > 0:
                time.sleep(sleep_for)

    def _scan_directory(
        self,
        directory: Path,
        relative_directory: PurePosixPath,
        entries: list[WatchSnapshotEntry],
    ) -> None:
        with os.scandir(directory) as iterator:
            children = sorted(iterator, key=lambda child: child.name)

        for child in children:
            relative_path = relative_directory / child.name
            if _is_ignored(relative_path, self._ignored_paths):
                continue

            absolute_path = directory / child.name
            if child.is_symlink():
                entries.append(_snapshot_symlink(absolute_path, relative_path))
            elif child.is_dir(follow_symlinks=False):
                self._scan_directory(
                    absolute_path,
                    relative_path,
                    entries,
                )
            elif child.is_file(follow_symlinks=False):
                entries.append(_snapshot_file(absolute_path, relative_path))


def _snapshot_file(
    path: Path,
    relative_path: PurePosixPath,
) -> WatchSnapshotEntry:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise WatchSnapshotError(f"Unable to open watched file '{path}'.") from exc

    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise WatchSnapshotError(f"Watched path '{path}' is not a regular file.")

        digest = hashlib.sha256()
        while chunk := os.read(descriptor, _READ_CHUNK_SIZE):
            digest.update(chunk)

        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)

    try:
        path_after = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise WatchSnapshotError(f"Watched file '{path}' changed while being snapshotted.") from exc

    if _stat_identity(before) != _stat_identity(after) or _stat_identity(after) != _stat_identity(
        path_after
    ):
        raise WatchSnapshotError(f"Watched file '{path}' changed while being snapshotted.")

    return WatchSnapshotEntry(
        relative_path,
        WatchPathKind.FILE,
        digest.hexdigest(),
    )


def _snapshot_symlink(
    path: Path,
    relative_path: PurePosixPath,
) -> WatchSnapshotEntry:
    try:
        before = path.lstat()
        target = os.readlink(path)
        after = path.lstat()
    except OSError as exc:
        message = f"Watched symlink '{path}' changed while being snapshotted."
        raise WatchSnapshotError(message) from exc

    if (
        not stat.S_ISLNK(before.st_mode)
        or not stat.S_ISLNK(after.st_mode)
        or _stat_identity(before) != _stat_identity(after)
    ):
        raise WatchSnapshotError(f"Watched symlink '{path}' changed while being snapshotted.")

    digest = hashlib.sha256(os.fsencode(target)).hexdigest()
    return WatchSnapshotEntry(
        relative_path,
        WatchPathKind.SYMLINK,
        digest,
    )


def _stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
    )


def _validate_watch_root(root: Path) -> Path:
    if not isinstance(root, Path):
        raise TypeError("Development watch root must be a pathlib.Path.")
    if not root.exists():
        raise InvalidWatchRootError(f"Development watch root '{root}' does not exist.")
    if root.is_symlink():
        raise InvalidWatchRootError(f"Development watch root '{root}' must not be a symlink.")
    if not root.is_dir():
        raise InvalidWatchRootError(f"Development watch root '{root}' must be a directory.")

    cursor = root.parent
    while True:
        if cursor.is_symlink():
            raise InvalidWatchRootError(
                f"Development watch root ancestor '{cursor}' must not be a symlink."
            )
        if cursor == cursor.parent:
            break
        cursor = cursor.parent

    return root.resolve(strict=True)


def _normalize_ignored_paths(
    paths: Iterable[PurePosixPath],
) -> tuple[PurePosixPath, ...]:
    try:
        normalized = tuple(paths)
    except TypeError as exc:
        raise TypeError("Ignored watch paths must be an iterable.") from exc

    for path in normalized:
        _validate_relative_path(path, label="Ignored watch path")

    ordered = tuple(sorted(set(normalized), key=lambda path: path.as_posix()))
    reduced: list[PurePosixPath] = []
    for path in ordered:
        if any(_path_is_within(path, parent) for parent in reduced):
            continue
        reduced.append(path)
    return tuple(reduced)


def _validate_relative_path(path: PurePosixPath, *, label: str) -> None:
    if not isinstance(path, PurePosixPath):
        raise TypeError(f"{label} must be a PurePosixPath.")
    if path.is_absolute() or not path.parts:
        raise ValueError(f"{label} must be a non-empty relative path.")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{label} must not contain empty, '.' or '..' segments.")


def _path_is_within(path: PurePosixPath, parent: PurePosixPath) -> bool:
    return path == parent or parent in path.parents


def _is_ignored(
    path: PurePosixPath,
    ignored_paths: tuple[PurePosixPath, ...],
) -> bool:
    return any(_path_is_within(path, ignored) for ignored in ignored_paths)


def _validate_interval(
    value: float,
    *,
    label: str,
    allow_zero: bool,
) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"Development watcher {label} must be a number.")

    normalized = float(value)
    minimum_valid = normalized >= 0 if allow_zero else normalized > 0
    if not minimum_valid:
        comparator = "non-negative" if allow_zero else "greater than zero"
        raise ValueError(f"Development watcher {label} must be {comparator}.")
    return normalized


__all__ = [
    "DevelopmentWatcher",
    "WatchChange",
    "WatchChangeBatch",
    "WatchChangeKind",
    "WatchPathKind",
    "WatchSnapshot",
    "WatchSnapshotEntry",
    "diff_watch_snapshots",
]
