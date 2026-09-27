"""Immutable in-memory build plan models."""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import PurePosixPath

from pypagekit.domain import Asset, Route
from pypagekit.exceptions import (
    BuildTargetCollisionError,
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
        _validate_target_type(self.target)
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
        normalized_pages = _normalize_entries(
            pages,
            expected_type=PageBuildEntry,
            owner="BuildPlan pages",
        )
        normalized_assets = _normalize_entries(
            assets,
            expected_type=AssetBuildEntry,
            owner="BuildPlan assets",
        )

        _validate_target_collisions(
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
    """Validate that planned file targets do not collide structurally."""

    normalized_targets = tuple(targets)
    for target in normalized_targets:
        _validate_target_type(target)
    _validate_target_collisions(normalized_targets)


def _normalize_entries(
    entries: Iterable[PageBuildEntry] | Iterable[AssetBuildEntry],
    *,
    expected_type: type[PageBuildEntry] | type[AssetBuildEntry],
    owner: str,
) -> tuple[PageBuildEntry, ...] | tuple[AssetBuildEntry, ...]:
    try:
        normalized = tuple(entries)
    except TypeError as exc:
        raise TypeError(f"{owner} must be an iterable.") from exc

    invalid = [entry for entry in normalized if not isinstance(entry, expected_type)]
    if invalid:
        invalid_type = type(invalid[0]).__name__
        raise TypeError(
            f"{owner} must contain only {expected_type.__name__} objects; "
            f"got {invalid_type}."
        )

    return normalized


def _validate_target_type(target: PurePosixPath) -> None:
    if not isinstance(target, PurePosixPath):
        raise InvalidBuildTargetError("Build target must be a PurePosixPath.")
    if target.is_absolute() or target == PurePosixPath("."):
        raise InvalidBuildTargetError(
            "Build target must be a non-empty path relative to the output root."
        )
    if any(part in {".", ".."} for part in target.parts):
        raise InvalidBuildTargetError("Build target must not contain traversal segments.")


def _validate_target_collisions(targets: tuple[PurePosixPath, ...]) -> None:
    for index, target in enumerate(targets):
        for other in targets[index + 1 :]:
            if _targets_conflict(target, other):
                raise BuildTargetCollisionError(
                    f"Build targets '{target.as_posix()}' and "
                    f"'{other.as_posix()}' conflict."
                )


def _targets_conflict(first: PurePosixPath, second: PurePosixPath) -> bool:
    if first == second:
        return True

    first_parts = first.parts
    second_parts = second.parts
    shared = min(len(first_parts), len(second_parts))

    return (
        first_parts[:shared] == second_parts[:shared]
        and len(first_parts) != len(second_parts)
    )
