"""Internal rollback transaction for local filesystem materialization."""

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class _FileMutation:
    destination: Path
    existed: bool
    backup: Path | None


class FilesystemTransactionRollbackError(Exception):
    """Internal signal that restoring filesystem state failed."""


class FilesystemTransaction:
    """Track file mutations and created directories for explicit rollback."""

    def __init__(self) -> None:
        self._mutations: list[_FileMutation] = []
        self._created_directories: list[Path] = []
        self._finished = False

    def ensure_directory(self, directory: Path) -> None:
        """Create missing directories one-by-one and remember them for rollback."""

        if self._finished:
            raise RuntimeError("Filesystem transaction is already finished.")

        missing: list[Path] = []
        cursor = directory
        while not cursor.exists():
            missing.append(cursor)
            if cursor == cursor.parent:
                break
            cursor = cursor.parent

        for candidate in reversed(missing):
            candidate.mkdir()
            self._created_directories.append(candidate)

    def prepare_file(
        self,
        destination: Path,
        *,
        backup_existing: bool,
        require_existing: bool = False,
    ) -> Path | None:
        """Snapshot an existing destination before it may be mutated."""

        if self._finished:
            raise RuntimeError("Filesystem transaction is already finished.")

        self.ensure_directory(destination.parent)
        existed = destination.exists()
        if require_existing and not existed:
            raise FileNotFoundError(
                f"Required transaction target '{destination}' no longer exists."
            )

        backup: Path | None = None

        if existed and backup_existing:
            descriptor, backup_name = tempfile.mkstemp(
                prefix=".pypagekit-backup-",
                suffix=".tmp",
                dir=destination.parent,
            )
            os.close(descriptor)
            backup = Path(backup_name)
            try:
                os.replace(destination, backup)
            except Exception:
                backup.unlink(missing_ok=True)
                raise

        self._mutations.append(
            _FileMutation(
                destination=destination,
                existed=existed,
                backup=backup,
            )
        )
        return backup

    def commit(self) -> None:
        """Finish the transaction and remove rollback snapshots."""

        if self._finished:
            raise RuntimeError("Filesystem transaction is already finished.")

        for mutation in self._mutations:
            if mutation.backup is not None:
                mutation.backup.unlink(missing_ok=True)

        self._finished = True

    def rollback(self) -> None:
        """Best-effort restore every mutated path in reverse order."""

        if self._finished:
            return

        failures: list[OSError] = []

        for mutation in reversed(self._mutations):
            try:
                if mutation.existed:
                    if mutation.backup is None:
                        continue
                    os.replace(mutation.backup, mutation.destination)
                else:
                    mutation.destination.unlink(missing_ok=True)
            except OSError as exc:
                failures.append(exc)

        for mutation in self._mutations:
            backup = mutation.backup
            if backup is None or not backup.exists():
                continue
            try:
                backup.unlink()
            except OSError as exc:
                failures.append(exc)

        for directory in reversed(self._created_directories):
            try:
                directory.rmdir()
            except FileNotFoundError:
                continue
            except OSError as exc:
                failures.append(exc)

        self._finished = True

        if failures:
            raise FilesystemTransactionRollbackError(
                f"Filesystem rollback failed in {len(failures)} operation(s)."
            ) from failures[0]


__all__ = [
    "FilesystemTransaction",
    "FilesystemTransactionRollbackError",
]
