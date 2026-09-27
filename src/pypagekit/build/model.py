"""Immutable in-memory build plan models."""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import PurePosixPath

from pypagekit.domain import Asset, Route
from pypagekit.domain.asset import validate_asset_target
from pypagekit.exceptions import (
    BuildTargetCollisionError,
    InvalidAssetTargetError,
    InvalidBuildContentError,
    InvalidBuildTargetError,
)


@dataclass(frozen=True, slots=True)
class PageBuildEntry:
    """Rendered page artifact planned for one output target."""

    route: Route
    target: PurePosixPath
    content: str

    def __post_init__(self) -> None:
        if not isinstance(self.route, Route):
            raise TypeError("Page build entry route must be a Route object.")
        _validate_build_target(self.target)
        if not isinstance(self.content, str):
            raise InvalidBuildContentError("Page build entry content must be a string.")


@dataclass(frozen=True, slots=True)
class AssetBuildEntry:
    """Asset copy operation planned for one output target."""

    asset: Asset

    def __post_init__(self) -> None:
        if not isinstance(self.asset, Asset):
            raise TypeError("Asset build entry asset must be an Asset object.")

    @property
    def target(self) -> PurePosixPath:
        """Return the publish target declared by the asset."""

        return self.asset.target


@dataclass(frozen=True, slots=True, init=False)
class BuildPlan:
    """Immutable build plan containing rendered pages and asset copy entries."""

    pages: tuple[PageBuildEntry, ...]
    assets: tuple[AssetBuildEntry, ...]

    def __init__(
        self,
        pages: Iterable[PageBuildEntry] = (),
        assets: Iterable[AssetBuildEntry] = (),
    ) -> None:
        normalized_pages = _normalize_page_entries(pages)
        normalized_assets = _normalize_asset_entries(assets)

        validate_build_targets(
            tuple(entry.target for entry in normalized_pages)
            + tuple(entry.target for entry in normalized_assets)
        )

        object.__setattr__(self, "pages", normalized_pages)
        object.__setattr__(self, "assets", normalized_assets)

    @property
    def page_targets(self) -> tuple[PurePosixPath, ...]:
        """Return page output targets in route declaration order."""

        return tuple(entry.target for entry in self.pages)

    @property
    def asset_targets(self) -> tuple[PurePosixPath, ...]:
        """Return asset output targets in declaration order."""

        return tuple(entry.target for entry in self.assets)

    @property
    def targets(self) -> tuple[PurePosixPath, ...]:
        """Return all planned targets, pages first then assets."""

        return self.page_targets + self.asset_targets


def validate_build_targets(targets: Iterable[PurePosixPath]) -> None:
    """Validate that planned file targets are safe and do not conflict."""

    normalized_targets = tuple(targets)
    for target in normalized_targets:
        _validate_build_target(target)
    _validate_target_collisions(normalized_targets)


def _normalize_page_entries(
    entries: Iterable[PageBuildEntry],
) -> tuple[PageBuildEntry, ...]:
    try:
        normalized = tuple(entries)
    except TypeError as exc:
        raise TypeError("BuildPlan pages must be an iterable.") from exc

    invalid = [entry for entry in normalized if not isinstance(entry, PageBuildEntry)]
    if invalid:
        invalid_type = type(invalid[0]).__name__
        raise TypeError(
            "BuildPlan pages must contain only PageBuildEntry objects; "
            f"got {invalid_type}."
        )

    return normalized


def _normalize_asset_entries(
    entries: Iterable[AssetBuildEntry],
) -> tuple[AssetBuildEntry, ...]:
    try:
        normalized = tuple(entries)
    except TypeError as exc:
        raise TypeError("BuildPlan assets must be an iterable.") from exc

    invalid = [entry for entry in normalized if not isinstance(entry, AssetBuildEntry)]
    if invalid:
        invalid_type = type(invalid[0]).__name__
        raise TypeError(
            "BuildPlan assets must contain only AssetBuildEntry objects; "
            f"got {invalid_type}."
        )

    return normalized


def _validate_build_target(target: PurePosixPath) -> None:
    try:
        validate_asset_target(target)
    except (TypeError, InvalidAssetTargetError) as exc:
        raise InvalidBuildTargetError(
            "Build target must be a safe output-root-relative PurePosixPath."
        ) from exc


def _validate_target_collisions(targets: tuple[PurePosixPath, ...]) -> None:
    seen_files: dict[tuple[str, ...], tuple[int, PurePosixPath]] = {}
    required_directories: dict[tuple[str, ...], tuple[int, PurePosixPath]] = {}
    best_conflict: tuple[int, int, PurePosixPath, PurePosixPath] | None = None

    for second_index, target in enumerate(targets):
        parts = target.parts
        candidates: list[tuple[int, PurePosixPath]] = []

        duplicate = seen_files.get(parts)
        if duplicate is not None:
            candidates.append(duplicate)

        ancestor = required_directories.get(parts)
        if ancestor is not None:
            candidates.append(ancestor)

        for depth in range(1, len(parts)):
            prefix_owner = seen_files.get(parts[:depth])
            if prefix_owner is not None:
                candidates.append(prefix_owner)

        if candidates:
            first_index, first_target = min(candidates, key=lambda item: item[0])
            conflict = (first_index, second_index, first_target, target)
            if best_conflict is None or conflict[:2] < best_conflict[:2]:
                best_conflict = conflict

        seen_files.setdefault(parts, (second_index, target))
        for depth in range(1, len(parts)):
            required_directories.setdefault(parts[:depth], (second_index, target))

    if best_conflict is not None:
        _, _, first, second = best_conflict
        raise BuildTargetCollisionError(
            f"Build targets '{first.as_posix()}' and '{second.as_posix()}' conflict."
        )
