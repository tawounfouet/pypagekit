"""Deterministic build fingerprints and immutable artifact manifests."""

from __future__ import annotations

import hashlib
import re
from bisect import bisect_left
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Self

from pypagekit.exceptions import (
    BuildManifestSourceError,
    InvalidBuildFingerprintError,
    InvalidBuildManifestError,
)

from .model import BuildPlan, validate_build_targets

_SHA256_ALGORITHM = "sha256"
_SHA256_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ASSET_READ_CHUNK_SIZE = 1024 * 1024
_MANIFEST_KINDS = frozenset({"page", "asset"})


@dataclass(frozen=True, slots=True)
class BuildFingerprint:
    """Content fingerprint for bytes that would be published by a build."""

    algorithm: str
    digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.algorithm, str):
            raise TypeError("Build fingerprint algorithm must be a string.")
        if self.algorithm != _SHA256_ALGORITHM:
            raise InvalidBuildFingerprintError(
                f"Unsupported build fingerprint algorithm: {self.algorithm!r}."
            )
        if not isinstance(self.digest, str):
            raise TypeError("Build fingerprint digest must be a string.")
        if _SHA256_DIGEST_RE.fullmatch(self.digest) is None:
            raise InvalidBuildFingerprintError(
                "Build fingerprint SHA-256 digest must contain exactly "
                "64 lowercase hexadecimal characters."
            )

    @classmethod
    def from_bytes(cls, content: bytes) -> Self:
        """Create a SHA-256 fingerprint from exact output bytes."""

        if not isinstance(content, bytes):
            raise TypeError("Build fingerprint byte content must be bytes.")
        return cls(_SHA256_ALGORITHM, hashlib.sha256(content).hexdigest())

    @classmethod
    def from_text(cls, content: str) -> Self:
        """Create a SHA-256 fingerprint from UTF-8 encoded output text."""

        if not isinstance(content, str):
            raise TypeError("Build fingerprint text content must be a string.")
        return cls.from_bytes(content.encode("utf-8"))

    def __str__(self) -> str:
        return f"{self.algorithm}:{self.digest}"


@dataclass(frozen=True, slots=True)
class BuildManifestEntry:
    """Fingerprint metadata for one planned output target."""

    target: PurePosixPath
    kind: str
    fingerprint: BuildFingerprint

    def __post_init__(self) -> None:
        validate_build_targets((self.target,))
        if not isinstance(self.kind, str):
            raise TypeError("Build manifest entry kind must be a string.")
        if self.kind not in _MANIFEST_KINDS:
            raise InvalidBuildManifestError(
                "Build manifest entry kind must be either 'page' or 'asset'."
            )
        if not isinstance(self.fingerprint, BuildFingerprint):
            raise TypeError(
                "Build manifest entry fingerprint must be a BuildFingerprint object."
            )


@dataclass(frozen=True, slots=True, init=False)
class BuildManifest:
    """Immutable ordered manifest of fingerprinted build targets."""

    entries: tuple[BuildManifestEntry, ...]
    _lookup_targets: tuple[str, ...] = field(
        init=False,
        repr=False,
        compare=False,
    )
    _lookup_entries: tuple[BuildManifestEntry, ...] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __init__(self, entries: Iterable[BuildManifestEntry] = ()) -> None:
        try:
            normalized = tuple(entries)
        except TypeError as exc:
            raise TypeError("Build manifest entries must be an iterable.") from exc

        invalid = [entry for entry in normalized if not isinstance(entry, BuildManifestEntry)]
        if invalid:
            invalid_type = type(invalid[0]).__name__
            raise TypeError(
                "Build manifest must contain only BuildManifestEntry objects; "
                f"got {invalid_type}."
            )

        validate_build_targets(tuple(entry.target for entry in normalized))

        ordered_lookup = tuple(
            sorted(
                ((entry.target.as_posix(), entry) for entry in normalized),
                key=lambda item: item[0],
            )
        )

        object.__setattr__(self, "entries", normalized)
        object.__setattr__(
            self,
            "_lookup_targets",
            tuple(target for target, _ in ordered_lookup),
        )
        object.__setattr__(
            self,
            "_lookup_entries",
            tuple(entry for _, entry in ordered_lookup),
        )

    @property
    def targets(self) -> tuple[PurePosixPath, ...]:
        """Return all manifest targets in build-plan order."""

        return tuple(entry.target for entry in self.entries)

    @property
    def page_entries(self) -> tuple[BuildManifestEntry, ...]:
        """Return page entries in build-plan order."""

        return tuple(entry for entry in self.entries if entry.kind == "page")

    @property
    def asset_entries(self) -> tuple[BuildManifestEntry, ...]:
        """Return asset entries in build-plan order."""

        return tuple(entry for entry in self.entries if entry.kind == "asset")

    @property
    def fingerprints(self) -> tuple[BuildFingerprint, ...]:
        """Return fingerprints in build-plan order."""

        return tuple(entry.fingerprint for entry in self.entries)

    def get(self, target: PurePosixPath) -> BuildManifestEntry | None:
        """Return the manifest entry for a target, or None when absent."""

        if not isinstance(target, PurePosixPath):
            raise TypeError("Build manifest lookup target must be a PurePosixPath.")

        key = target.as_posix()
        index = bisect_left(self._lookup_targets, key)
        if index >= len(self._lookup_targets) or self._lookup_targets[index] != key:
            return None
        return self._lookup_entries[index]

    def has_target(self, target: PurePosixPath) -> bool:
        """Return whether the manifest contains one target."""

        return self.get(target) is not None

    def __iter__(self) -> Iterator[BuildManifestEntry]:
        return iter(self.entries)

    def __len__(self) -> int:
        return len(self.entries)


def build_manifest(plan: BuildPlan) -> BuildManifest:
    """Fingerprint a build plan, reading asset source bytes explicitly."""

    if not isinstance(plan, BuildPlan):
        raise TypeError("build_manifest() requires a BuildPlan object.")

    entries: list[BuildManifestEntry] = []

    for page_entry in plan.pages:
        entries.append(
            BuildManifestEntry(
                target=page_entry.target,
                kind="page",
                fingerprint=BuildFingerprint.from_text(page_entry.content),
            )
        )

    for asset_entry in plan.assets:
        entries.append(
            BuildManifestEntry(
                target=asset_entry.target,
                kind="asset",
                fingerprint=_fingerprint_asset_source(asset_entry.asset.source),
            )
        )

    return BuildManifest(entries)


def _fingerprint_asset_source(source: Path) -> BuildFingerprint:
    if source.is_symlink() and not source.exists():
        raise BuildManifestSourceError(
            f"Asset source '{source}' is a broken symlink and cannot be fingerprinted."
        )
    if not source.exists():
        raise BuildManifestSourceError(
            f"Asset source '{source}' does not exist and cannot be fingerprinted."
        )
    if not source.is_file():
        raise BuildManifestSourceError(
            f"Asset source '{source}' must be a regular file to be fingerprinted."
        )

    try:
        before = _source_state(source)
        digest = hashlib.sha256()
        with source.open("rb") as source_file:
            while chunk := source_file.read(_ASSET_READ_CHUNK_SIZE):
                digest.update(chunk)
        after = _source_state(source)
    except OSError as exc:
        raise BuildManifestSourceError(
            f"Asset source '{source}' could not be fingerprinted."
        ) from exc

    if before != after:
        raise BuildManifestSourceError(
            f"Asset source '{source}' changed while its fingerprint was being computed."
        )

    return BuildFingerprint(_SHA256_ALGORITHM, digest.hexdigest())


def _source_state(source: Path) -> tuple[int, int, int, int]:
    stat = source.stat()
    return (
        stat.st_dev,
        stat.st_ino,
        stat.st_size,
        stat.st_mtime_ns,
    )


__all__ = [
    "BuildFingerprint",
    "BuildManifest",
    "BuildManifestEntry",
    "build_manifest",
]
