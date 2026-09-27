"""Declarative static assets for future build planning."""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

from pypagekit.exceptions import (
    DuplicateAssetTargetError,
    InvalidAssetSourceError,
    InvalidAssetTargetError,
    UnknownAssetTargetError,
)

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_PERCENT_ESCAPE_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")


def validate_asset_target(target: PurePosixPath) -> None:
    """Validate an output-root-relative portable POSIX target path."""

    if not isinstance(target, PurePosixPath) or isinstance(target, Path):
        raise TypeError("Asset target must be a pathlib.PurePosixPath.")
    if target.is_absolute():
        raise InvalidAssetTargetError("Asset target must be relative to the output root.")
    if target == PurePosixPath("."):
        raise InvalidAssetTargetError("Asset target must not be empty.")
    if any(part == ".." for part in target.parts):
        raise InvalidAssetTargetError("Asset target must not contain '..' segments.")

    serialized = target.as_posix()
    if "\\" in serialized:
        raise InvalidAssetTargetError("Asset target must use POSIX separators only.")
    if _CONTROL_RE.search(serialized):
        raise InvalidAssetTargetError("Asset target must not contain control characters.")
    if "?" in serialized or "#" in serialized:
        raise InvalidAssetTargetError(
            "Asset target must be a path, not a URL with query or fragment."
        )
    if ":" in serialized:
        raise InvalidAssetTargetError("Asset target must not contain ':' characters.")
    if _PERCENT_ESCAPE_RE.search(serialized):
        raise InvalidAssetTargetError("Asset target contains an invalid percent escape.")

    decoded = unquote(serialized)
    if _CONTROL_RE.search(decoded):
        raise InvalidAssetTargetError("Asset target must not encode control characters.")
    if "\\" in decoded:
        raise InvalidAssetTargetError("Asset target must not encode backslash separators.")
    if decoded.count("/") != serialized.count("/"):
        raise InvalidAssetTargetError("Asset target must not encode slash separators.")

    decoded_parts = PurePosixPath(decoded).parts
    if any(part in {".", ".."} for part in decoded_parts):
        raise InvalidAssetTargetError("Asset target must not encode '.' or '..' path segments.")


@dataclass(frozen=True, slots=True)
class Asset:
    """Immutable declaration of one source resource and publish target."""

    source: Path
    target: PurePosixPath

    def __post_init__(self) -> None:
        if not isinstance(self.source, Path):
            raise InvalidAssetSourceError("Asset source must be a pathlib.Path object.")
        validate_asset_target(self.target)

    @property
    def public_path(self) -> str:
        """Return the root-relative public reference for this target."""

        return f"/{self.target.as_posix()}"


@dataclass(frozen=True, slots=True, init=False)
class Assets:
    """Immutable validated collection of asset declarations."""

    items: tuple[Asset, ...]

    def __init__(self, items: Iterable[Asset] = ()) -> None:
        try:
            normalized_items = tuple(items)
        except TypeError as exc:
            raise TypeError("Assets items must be an iterable of Asset objects.") from exc

        invalid_items = [item for item in normalized_items if not isinstance(item, Asset)]
        if invalid_items:
            invalid_type = type(invalid_items[0]).__name__
            raise InvalidAssetSourceError(
                f"Assets must contain only Asset objects; got {invalid_type}."
            )

        seen_targets: set[PurePosixPath] = set()
        for asset in normalized_items:
            if asset.target in seen_targets:
                raise DuplicateAssetTargetError(
                    f"Asset target '{asset.target.as_posix()}' appears more than once."
                )
            seen_targets.add(asset.target)

        object.__setattr__(self, "items", normalized_items)

    @property
    def targets(self) -> tuple[PurePosixPath, ...]:
        """Return asset targets in declaration order."""

        return tuple(asset.target for asset in self.items)

    @property
    def public_paths(self) -> tuple[str, ...]:
        """Return public asset references in declaration order."""

        return tuple(asset.public_path for asset in self.items)

    def has_target(self, target: PurePosixPath) -> bool:
        """Return whether a target exists in this asset set."""

        validate_asset_target(target)
        return any(asset.target == target for asset in self.items)

    def asset(self, target: PurePosixPath) -> Asset:
        """Look up an asset by its validated target path."""

        validate_asset_target(target)
        for asset in self.items:
            if asset.target == target:
                return asset

        raise UnknownAssetTargetError(f"Asset target '{target.as_posix()}' is not declared.")
