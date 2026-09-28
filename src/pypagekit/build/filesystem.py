"""Filesystem materialization for qualified build plans."""

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Never

from pypagekit._filesystem_transaction import (
    FilesystemTransaction,
    FilesystemTransactionRollbackError,
)
from pypagekit.exceptions import (
    AssetSourceOutputConflictError,
    ExistingOutputError,
    FilesystemRollbackError,
    FilesystemWriteError,
    IncrementalOutputDriftError,
    InvalidAssetSourceForOutputError,
    InvalidOutputRootError,
    OutputPathConflictError,
    OutputSymlinkError,
)

from .manifest import (
    BuildFingerprint,
    BuildManifest,
    BuildManifestDiff,
    BuildManifestEntry,
    build_manifest,
    diff_build_manifests,
)
from .model import BuildPlan

_FINGERPRINT_READ_CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True, slots=True)
class FilesystemWriteResult:
    """Immutable record of files materialized from one build plan."""

    output_root: Path
    page_files: tuple[Path, ...]
    asset_files: tuple[Path, ...]

    @property
    def files(self) -> tuple[Path, ...]:
        """Return every written file, pages first then assets."""

        return self.page_files + self.asset_files


@dataclass(frozen=True, slots=True)
class IncrementalFilesystemWriteResult:
    """Immutable result of applying one incremental build transition."""

    output_root: Path
    manifest: BuildManifest
    diff: BuildManifestDiff
    added_files: tuple[Path, ...]
    changed_files: tuple[Path, ...]
    removed_files: tuple[Path, ...]
    unchanged_files: tuple[Path, ...]

    @property
    def written_files(self) -> tuple[Path, ...]:
        """Return physically written files in resulting build-plan order."""

        written_targets = set(self.diff.added_targets) | set(self.diff.changed_targets)
        return tuple(
            _destination(self.output_root, entry.target)
            for entry in self.manifest.entries
            if entry.target in written_targets
        )

    @property
    def files(self) -> tuple[Path, ...]:
        """Return every file represented by the resulting manifest."""

        return tuple(
            _destination(self.output_root, target) for target in self.manifest.targets
        )


class FilesystemWriter:
    """Materialize a BuildPlan under an explicit output root."""

    def write(
        self,
        plan: BuildPlan,
        output_root: Path,
        *,
        overwrite: bool = False,
    ) -> FilesystemWriteResult:
        """Preflight and materialize a build plan on the local filesystem."""

        if not isinstance(plan, BuildPlan):
            raise TypeError("Filesystem writer plan must be a BuildPlan object.")
        if not isinstance(output_root, Path):
            raise TypeError("Filesystem writer output_root must be a pathlib.Path.")
        if not isinstance(overwrite, bool):
            raise TypeError("Filesystem writer overwrite flag must be a bool.")

        self._preflight(plan, output_root, overwrite=overwrite)

        transaction = FilesystemTransaction()
        page_files: list[Path] = []
        asset_files: list[Path] = []

        try:
            transaction.ensure_directory(output_root)

            for page_entry in plan.pages:
                destination = _destination(output_root, page_entry.target)
                transaction.prepare_file(
                    destination,
                    backup_existing=overwrite,
                )
                text_mode = "w" if overwrite else "x"
                with destination.open(
                    text_mode,
                    encoding="utf-8",
                    newline="",
                ) as output_file:
                    output_file.write(page_entry.content)
                page_files.append(destination)

            for asset_entry in plan.assets:
                destination = _destination(output_root, asset_entry.target)
                transaction.prepare_file(
                    destination,
                    backup_existing=overwrite,
                )
                binary_mode = "wb" if overwrite else "xb"
                with (
                    asset_entry.asset.source.open("rb") as source_file,
                    destination.open(binary_mode) as output_file,
                ):
                    shutil.copyfileobj(source_file, output_file)
                asset_files.append(destination)

            transaction.commit()
        except Exception as exc:
            _rollback_or_raise(transaction, output_root, exc)

        return FilesystemWriteResult(
            output_root=output_root,
            page_files=tuple(page_files),
            asset_files=tuple(asset_files),
        )

    def write_incremental(
        self,
        plan: BuildPlan,
        previous_manifest: BuildManifest,
        output_root: Path,
    ) -> IncrementalFilesystemWriteResult:
        """Apply only added, changed, and removed artifacts for a build plan."""

        if not isinstance(plan, BuildPlan):
            raise TypeError("Incremental writer plan must be a BuildPlan object.")
        if not isinstance(previous_manifest, BuildManifest):
            raise TypeError(
                "Incremental writer previous_manifest must be a BuildManifest object."
            )
        if not isinstance(output_root, Path):
            raise TypeError("Incremental writer output_root must be a pathlib.Path.")

        current_manifest = build_manifest(plan)
        diff = diff_build_manifests(previous_manifest, current_manifest)
        self._preflight_incremental(
            plan,
            previous_manifest,
            current_manifest,
            diff,
            output_root,
        )

        added_targets = set(diff.added_targets)
        changed_targets = set(diff.changed_targets)
        write_targets = added_targets | changed_targets

        added_files = tuple(
            _destination(output_root, entry.target) for entry in diff.added
        )
        changed_files = tuple(
            _destination(output_root, entry.target) for entry in diff.changed
        )
        removed_files = tuple(
            _destination(output_root, entry.target) for entry in diff.removed
        )
        unchanged_files = tuple(
            _destination(output_root, entry.target) for entry in diff.unchanged
        )

        if not diff.has_changes:
            return IncrementalFilesystemWriteResult(
                output_root=output_root,
                manifest=current_manifest,
                diff=diff,
                added_files=(),
                changed_files=(),
                removed_files=(),
                unchanged_files=unchanged_files,
            )

        transaction = FilesystemTransaction()

        try:
            transaction.ensure_directory(output_root)

            for entry in diff.removed:
                destination = _destination(output_root, entry.target)
                _prepare_tracked_file(
                    transaction,
                    destination,
                    entry,
                )

            for page_entry in plan.pages:
                if page_entry.target not in write_targets:
                    continue

                destination = _destination(output_root, page_entry.target)
                is_changed = page_entry.target in changed_targets
                if is_changed:
                    previous_entry = previous_manifest.get(page_entry.target)
                    if previous_entry is None:
                        raise RuntimeError(
                            "Changed page target is missing from previous manifest."
                        )
                    _prepare_tracked_file(
                        transaction,
                        destination,
                        previous_entry,
                    )
                else:
                    transaction.prepare_file(
                        destination,
                        backup_existing=False,
                    )
                with destination.open(
                    "x",
                    encoding="utf-8",
                    newline="",
                ) as output_file:
                    output_file.write(page_entry.content)

            for asset_entry in plan.assets:
                if asset_entry.target not in write_targets:
                    continue

                destination = _destination(output_root, asset_entry.target)
                is_changed = asset_entry.target in changed_targets
                if is_changed:
                    previous_entry = previous_manifest.get(asset_entry.target)
                    if previous_entry is None:
                        raise RuntimeError(
                            "Changed asset target is missing from previous manifest."
                        )
                    _prepare_tracked_file(
                        transaction,
                        destination,
                        previous_entry,
                    )
                else:
                    transaction.prepare_file(
                        destination,
                        backup_existing=False,
                    )
                with (
                    asset_entry.asset.source.open("rb") as source_file,
                    destination.open("xb") as output_file,
                ):
                    shutil.copyfileobj(source_file, output_file)

            for entry in (*diff.added, *diff.changed):
                destination = _destination(output_root, entry.target)
                fingerprint = _fingerprint_materialized_file(destination)
                if fingerprint != entry.fingerprint:
                    raise OSError(
                        f"Incremental output '{destination}' does not match its "
                        "planned fingerprint."
                    )

            transaction.commit()
        except Exception as exc:
            _rollback_or_raise(transaction, output_root, exc)

        return IncrementalFilesystemWriteResult(
            output_root=output_root,
            manifest=current_manifest,
            diff=diff,
            added_files=added_files,
            changed_files=changed_files,
            removed_files=removed_files,
            unchanged_files=unchanged_files,
        )

    def _preflight(
        self,
        plan: BuildPlan,
        output_root: Path,
        *,
        overwrite: bool,
    ) -> None:
        _validate_output_root_symlinks(output_root)
        _validate_output_root(output_root)

        destinations = tuple(
            _destination(output_root, target) for target in plan.targets
        )

        _validate_asset_sources_against_destinations(
            plan,
            destinations,
        )

        for destination in destinations:
            _validate_destination(
                output_root,
                destination,
                overwrite=overwrite,
            )

    def _preflight_incremental(
        self,
        plan: BuildPlan,
        previous_manifest: BuildManifest,
        current_manifest: BuildManifest,
        diff: BuildManifestDiff,
        output_root: Path,
    ) -> None:
        _validate_output_root_symlinks(output_root)
        _validate_output_root(output_root)

        if previous_manifest.entries and not output_root.exists():
            raise IncrementalOutputDriftError(
                f"Incremental output root '{output_root}' is missing."
            )

        for entry in previous_manifest.entries:
            destination = _destination(output_root, entry.target)
            _validate_destination(
                output_root,
                destination,
                overwrite=True,
            )
            if not destination.exists():
                raise IncrementalOutputDriftError(
                    f"Tracked output '{destination}' is missing."
                )
            if not destination.is_file():
                raise IncrementalOutputDriftError(
                    f"Tracked output '{destination}' is not a regular file."
                )

            try:
                actual = _fingerprint_materialized_file(destination)
            except OSError as exc:
                raise IncrementalOutputDriftError(
                    f"Tracked output '{destination}' could not be verified."
                ) from exc

            if actual != entry.fingerprint:
                raise IncrementalOutputDriftError(
                    f"Tracked output '{destination}' no longer matches "
                    "the previous build manifest."
                )

        for entry in diff.added:
            destination = _destination(output_root, entry.target)
            _validate_destination(
                output_root,
                destination,
                overwrite=False,
            )

        mutation_destinations = tuple(
            _destination(output_root, target)
            for target in (
                current_manifest.targets + diff.removed_targets
            )
        )
        _validate_asset_sources_against_destinations(
            plan,
            mutation_destinations,
        )


def _prepare_tracked_file(
    transaction: FilesystemTransaction,
    destination: Path,
    previous_entry: BuildManifestEntry,
) -> None:
    try:
        backup = transaction.prepare_file(
            destination,
            backup_existing=True,
            require_existing=True,
        )
    except FileNotFoundError as exc:
        raise IncrementalOutputDriftError(
            f"Tracked output '{destination}' disappeared before mutation."
        ) from exc

    _verify_transaction_backup(previous_entry, backup, destination)


def _verify_transaction_backup(
    previous_entry: BuildManifestEntry,
    backup: Path | None,
    destination: Path,
) -> None:
    if backup is None:
        raise IncrementalOutputDriftError(
            f"Tracked output '{destination}' disappeared before mutation."
        )

    try:
        actual = _fingerprint_materialized_file(backup)
    except OSError as exc:
        raise IncrementalOutputDriftError(
            f"Tracked output '{destination}' could not be verified after backup."
        ) from exc

    if actual != previous_entry.fingerprint:
        raise IncrementalOutputDriftError(
            f"Tracked output '{destination}' changed immediately before mutation."
        )


def _rollback_or_raise(
    transaction: FilesystemTransaction,
    output_root: Path,
    exc: Exception,
) -> Never:
    try:
        transaction.rollback()
    except FilesystemTransactionRollbackError as rollback_exc:
        raise FilesystemRollbackError(
            f"Filesystem rollback failed under '{output_root}' after "
            f"{type(exc).__name__}."
        ) from rollback_exc

    if isinstance(exc, IncrementalOutputDriftError):
        raise exc

    raise FilesystemWriteError(
        f"Filesystem output failed under '{output_root}'."
    ) from exc


def _destination(output_root: Path, target: PurePosixPath) -> Path:
    return output_root.joinpath(*target.parts)


def _fingerprint_materialized_file(path: Path) -> BuildFingerprint:
    before = path.stat(follow_symlinks=False)
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        while chunk := input_file.read(_FINGERPRINT_READ_CHUNK_SIZE):
            digest.update(chunk)
    after = path.stat(follow_symlinks=False)

    before_state = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    after_state = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if before_state != after_state:
        raise OSError(f"File '{path}' changed during fingerprint verification.")

    return BuildFingerprint("sha256", digest.hexdigest())


def _validate_asset_sources_against_destinations(
    plan: BuildPlan,
    destinations: tuple[Path, ...],
) -> None:
    resolved_destinations = {
        destination.resolve(strict=False) for destination in destinations
    }
    destination_identities: dict[tuple[int, int], Path] = {}
    for destination in destinations:
        if (
            destination.is_symlink()
            or not destination.exists()
            or not destination.is_file()
        ):
            continue
        stat = destination.stat(follow_symlinks=False)
        destination_identities.setdefault((stat.st_dev, stat.st_ino), destination)

    for entry in plan.assets:
        source = entry.asset.source
        if source.is_symlink() and not source.exists():
            raise InvalidAssetSourceForOutputError(
                f"Asset source '{source}' is a broken symlink."
            )
        if not source.exists():
            raise InvalidAssetSourceForOutputError(
                f"Asset source '{source}' does not exist."
            )
        if not source.is_file():
            raise InvalidAssetSourceForOutputError(
                f"Asset source '{source}' must be a regular file."
            )

        if source.resolve() in resolved_destinations:
            raise AssetSourceOutputConflictError(
                f"Asset source '{source}' is also a planned output destination."
            )

        source_stat = source.stat()
        conflicting_destination = destination_identities.get(
            (source_stat.st_dev, source_stat.st_ino)
        )
        if conflicting_destination is not None:
            raise AssetSourceOutputConflictError(
                f"Asset source '{source}' shares an inode with planned output "
                f"destination '{conflicting_destination}'."
            )


def _validate_output_root_symlinks(output_root: Path) -> None:
    cursor = output_root
    while True:
        if cursor.is_symlink():
            raise OutputSymlinkError(
                f"Output root path '{cursor}' must not traverse a symlink."
            )
        if cursor == cursor.parent:
            break
        cursor = cursor.parent


def _validate_output_root(output_root: Path) -> None:
    if output_root.is_symlink():
        raise OutputSymlinkError(
            f"Output root '{output_root}' must not be a symlink."
        )
    if output_root.exists() and not output_root.is_dir():
        raise InvalidOutputRootError(
            f"Output root '{output_root}' must be a directory."
        )


def _validate_destination(
    output_root: Path,
    destination: Path,
    *,
    overwrite: bool,
) -> None:
    relative = destination.relative_to(output_root)
    cursor = output_root

    for part in relative.parts[:-1]:
        cursor = cursor / part
        if cursor.is_symlink():
            raise OutputSymlinkError(
                f"Output path ancestor '{cursor}' must not be a symlink."
            )
        if cursor.exists() and not cursor.is_dir():
            raise OutputPathConflictError(
                f"Output path ancestor '{cursor}' is not a directory."
            )

    if destination.is_symlink():
        raise OutputSymlinkError(
            f"Output target '{destination}' must not be a symlink."
        )

    if destination.exists():
        if destination.is_dir():
            raise OutputPathConflictError(
                f"Output target '{destination}' is an existing directory."
            )
        if overwrite and destination.stat(follow_symlinks=False).st_nlink > 1:
            raise OutputPathConflictError(
                f"Output target '{destination}' must not be a hard-linked file."
            )
        if not overwrite:
            raise ExistingOutputError(
                f"Output target '{destination}' already exists."
            )
