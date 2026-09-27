from dataclasses import FrozenInstanceError
from pathlib import Path, PurePosixPath

import pytest

from pypagekit import Asset, Assets
from pypagekit.exceptions import (
    DuplicateAssetTargetError,
    InvalidAssetSourceError,
    InvalidAssetTargetError,
    UnknownAssetTargetError,
)


def test_asset_preserves_source_and_target() -> None:
    source = Path("static/logo.png")
    target = PurePosixPath("assets/logo.png")
    asset = Asset(source, target)

    assert asset.source == source
    assert asset.target == target
    assert asset.public_path == "/assets/logo.png"


def test_asset_does_not_require_source_to_exist() -> None:
    asset = Asset(
        Path("does-not-exist/logo.png"),
        PurePosixPath("assets/logo.png"),
    )

    assert asset.source == Path("does-not-exist/logo.png")


def test_asset_allows_absolute_source_without_io() -> None:
    asset = Asset(
        Path("/tmp/project/logo.png"),
        PurePosixPath("assets/logo.png"),
    )

    assert asset.source.is_absolute()


def test_asset_is_immutable() -> None:
    asset = Asset(Path("logo.png"), PurePosixPath("assets/logo.png"))

    with pytest.raises(FrozenInstanceError):
        asset.source = Path("changed.png")  # type: ignore[misc]


def test_asset_source_must_be_path() -> None:
    with pytest.raises(InvalidAssetSourceError):
        Asset("logo.png", PurePosixPath("assets/logo.png"))  # type: ignore[arg-type]


def test_asset_target_must_be_pure_posix_path() -> None:
    with pytest.raises(TypeError, match="PurePosixPath"):
        Asset(Path("logo.png"), Path("assets/logo.png"))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "target",
    [
        PurePosixPath("/assets/logo.png"),
        PurePosixPath("."),
        PurePosixPath("../logo.png"),
        PurePosixPath("assets/../logo.png"),
        PurePosixPath("assets\\logo.png"),
        PurePosixPath("assets/logo.png?version=1"),
        PurePosixPath("assets/logo.png#icon"),
        PurePosixPath("assets/C:logo.png"),
        PurePosixPath("assets/bad%escape.png"),
        PurePosixPath("assets/%2Flogo.png"),
        PurePosixPath("assets/%5Clogo.png"),
        PurePosixPath("assets/%00logo.png"),
        PurePosixPath("assets/%2e%2e/logo.png"),
    ],
)
def test_asset_rejects_invalid_or_ambiguous_targets(target: PurePosixPath) -> None:
    with pytest.raises(InvalidAssetTargetError):
        Asset(Path("logo.png"), target)


def test_assets_can_be_empty() -> None:
    assets = Assets()

    assert assets.items == ()
    assert assets.targets == ()
    assert assets.public_paths == ()


def test_assets_preserve_declaration_order() -> None:
    logo = Asset(Path("logo.png"), PurePosixPath("assets/logo.png"))
    app = Asset(Path("app.js"), PurePosixPath("assets/app.js"))

    assets = Assets([logo, app])

    assert assets.items == (logo, app)
    assert assets.targets == (
        PurePosixPath("assets/logo.png"),
        PurePosixPath("assets/app.js"),
    )
    assert assets.public_paths == (
        "/assets/logo.png",
        "/assets/app.js",
    )


def test_assets_accept_generator() -> None:
    assets = Assets(
        Asset(
            Path(f"file-{index}.txt"),
            PurePosixPath(f"assets/file-{index}.txt"),
        )
        for index in range(2)
    )

    assert len(assets.items) == 2


def test_assets_reject_duplicate_target() -> None:
    with pytest.raises(DuplicateAssetTargetError, match=r"assets/logo\.png"):
        Assets(
            [
                Asset(Path("logo-a.png"), PurePosixPath("assets/logo.png")),
                Asset(Path("logo-b.png"), PurePosixPath("assets/logo.png")),
            ]
        )


def test_assets_allow_same_source_for_distinct_targets() -> None:
    source = Path("logo.png")
    assets = Assets(
        [
            Asset(source, PurePosixPath("assets/logo.png")),
            Asset(source, PurePosixPath("images/logo.png")),
        ]
    )

    assert len(assets.items) == 2


def test_assets_reject_invalid_member() -> None:
    with pytest.raises(InvalidAssetSourceError, match="Asset objects"):
        Assets(["invalid"])  # type: ignore[list-item]


def test_asset_lookup_returns_canonical_asset_object() -> None:
    logo = Asset(Path("logo.png"), PurePosixPath("assets/logo.png"))
    assets = Assets([logo])

    assert assets.asset(PurePosixPath("assets/logo.png")) is logo
    assert assets.has_target(PurePosixPath("assets/logo.png"))


def test_unknown_asset_target_fails_explicitly() -> None:
    assets = Assets()

    with pytest.raises(UnknownAssetTargetError, match=r"assets/missing\.png"):
        assets.asset(PurePosixPath("assets/missing.png"))


def test_has_target_returns_false_for_valid_unknown_target() -> None:
    assert not Assets().has_target(PurePosixPath("assets/missing.png"))
