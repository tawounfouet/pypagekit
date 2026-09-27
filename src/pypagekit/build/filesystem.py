"""Filesystem materialization for qualified build plans."""

import shutil
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from pypagekit.exceptions import (
    AssetSourceOutputConflictError,
    ExistingOutputError,
    FilesystemWriteError,
    InvalidAssetSourceForOutputError,
    InvalidOutputRootError,
    OutputPathConflictError,
    OutputSymlinkError,
)

from .model import BuildPlan


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

        try:
            output_root.mkdir(parents=True, exist_ok=True)

            page_files: list[Path] = []
            for page_entry in plan.pages:
                destination = _destination(output_root, page_entry.target)
                destination.parent.mkdir(parents=True, exist_ok=True)
                text_mode = "w" if overwrite else "x"
                with destination.open(
                    text_mode,
                    encoding="utf-8",
                    newline="",
                ) as output_file:
                    output_file.write(page_entry.content)
                page_files.append(destination)

            asset_files: list[Path] = []
            for asset_entry in plan.assets:
                destination = _destination(output_root, asset_entry.target)
                destination.parent.mkdir(parents=True, exist_ok=True)
                binary_mode = "wb" if overwrite else "xb"
                with (
                    asset_entry.asset.source.open("rb") as source_file,
                    destination.open(binary_mode) as output_file,
                ):
                    shutil.copyfileobj(source_file, output_file)
                asset_files.append(destination)
        except OSError as exc:
            raise FilesystemWriteError(
                f"Filesystem output failed under '{output_root}'."
            ) from exc

        return FilesystemWriteResult(
            output_root=output_root,
            page_files=tuple(page_files),
            asset_files=tuple(asset_files),
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
            _destination(output_root, target)
            for target in plan.targets
        )

        for destination in destinations:
            _validate_destination(
                output_root,
                destination,
                overwrite=overwrite,
            )

        resolved_destinations = {
            destination.resolve(strict=False) for destination in destinations
        }

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

            for destination in destinations:
                if destination.exists() and source.samefile(destination):
                    raise AssetSourceOutputConflictError(
                        f"Asset source '{source}' shares an inode with planned output "
                        f"destination '{destination}'."
                    )


def _destination(output_root: Path, target: PurePosixPath) -> Path:
    return output_root.joinpath(*target.parts)


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
