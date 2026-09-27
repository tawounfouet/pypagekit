from pathlib import Path, PurePosixPath

import pytest

from pypagekit import Asset
from pypagekit.exceptions import InvalidAssetTargetError


@pytest.mark.parametrize(
    "target",
    [
        PurePosixPath("../outside.txt"),
        PurePosixPath("assets/%2e%2e/outside.txt"),
        PurePosixPath("assets/%2Foutside.txt"),
        PurePosixPath("assets/%5Coutside.txt"),
        PurePosixPath("assets/file.txt?next=/outside"),
        PurePosixPath("assets/file.txt#fragment"),
    ],
)
def test_asset_target_cannot_escape_or_confuse_future_output_root(
    target: PurePosixPath,
) -> None:
    with pytest.raises(InvalidAssetTargetError):
        Asset(Path("source.txt"), target)


def test_asset_public_path_is_root_relative_and_deterministic() -> None:
    asset = Asset(
        Path("static/app.css"),
        PurePosixPath("assets/css/app.css"),
    )

    assert asset.public_path == "/assets/css/app.css"


def test_asset_model_performs_no_filesystem_operation() -> None:
    source = Path("/definitely/not/a/real/path/file.css")

    asset = Asset(source, PurePosixPath("assets/file.css"))

    assert asset.source is source
    assert not hasattr(asset, "copy")
    assert not hasattr(asset, "write")
