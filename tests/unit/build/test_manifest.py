from dataclasses import FrozenInstanceError
from pathlib import Path, PurePosixPath

import pytest

from pypagekit import Asset, Page, Route
from pypagekit.build import (
    AssetBuildEntry,
    BuildFingerprint,
    BuildManifest,
    BuildManifestEntry,
    BuildPlan,
    PageBuildEntry,
    build_manifest,
)
from pypagekit.exceptions import (
    BuildManifestSourceError,
    BuildTargetCollisionError,
    InvalidBuildFingerprintError,
    InvalidBuildManifestError,
)


def test_build_fingerprint_from_bytes_uses_sha256() -> None:
    fingerprint = BuildFingerprint.from_bytes(b"hello")

    assert fingerprint == BuildFingerprint(
        "sha256",
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
    )
    assert str(fingerprint) == (
        "sha256:2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )


def test_build_fingerprint_from_text_uses_utf8_bytes() -> None:
    assert BuildFingerprint.from_text("café") == BuildFingerprint.from_bytes(
        "café".encode("utf-8")
    )


@pytest.mark.parametrize(
    ("algorithm", "digest"),
    [
        ("sha1", "0" * 64),
        ("sha256", "0" * 63),
        ("sha256", "A" * 64),
        ("sha256", "g" * 64),
    ],
)
def test_build_fingerprint_rejects_invalid_values(
    algorithm: str,
    digest: str,
) -> None:
    with pytest.raises(InvalidBuildFingerprintError):
        BuildFingerprint(algorithm, digest)


def test_build_fingerprint_is_immutable() -> None:
    fingerprint = BuildFingerprint.from_bytes(b"content")

    with pytest.raises(FrozenInstanceError):
        fingerprint.digest = "0" * 64  # type: ignore[misc]


def test_build_manifest_entry_validates_kind_and_fingerprint() -> None:
    fingerprint = BuildFingerprint.from_bytes(b"content")

    with pytest.raises(InvalidBuildManifestError):
        BuildManifestEntry(PurePosixPath("index.html"), "unknown", fingerprint)

    with pytest.raises(TypeError):
        BuildManifestEntry(
            PurePosixPath("index.html"),
            "page",
            "invalid",  # type: ignore[arg-type]
        )


def test_build_manifest_preserves_plan_order_and_supports_lookup() -> None:
    page = BuildManifestEntry(
        PurePosixPath("index.html"),
        "page",
        BuildFingerprint.from_text("<html></html>"),
    )
    asset = BuildManifestEntry(
        PurePosixPath("assets/app.css"),
        "asset",
        BuildFingerprint.from_bytes(b"body{}"),
    )

    manifest = BuildManifest([page, asset])

    assert manifest.entries == (page, asset)
    assert manifest.targets == (
        PurePosixPath("index.html"),
        PurePosixPath("assets/app.css"),
    )
    assert manifest.page_entries == (page,)
    assert manifest.asset_entries == (asset,)
    assert manifest.fingerprints == (page.fingerprint, asset.fingerprint)
    assert manifest.get(PurePosixPath("index.html")) is page
    assert manifest.get(PurePosixPath("missing.html")) is None
    assert manifest.has_target(PurePosixPath("assets/app.css")) is True
    assert manifest.has_target(PurePosixPath("missing.html")) is False
    assert tuple(manifest) == (page, asset)
    assert len(manifest) == 2


def test_build_manifest_rejects_conflicting_targets() -> None:
    first = BuildManifestEntry(
        PurePosixPath("docs"),
        "asset",
        BuildFingerprint.from_bytes(b"first"),
    )
    second = BuildManifestEntry(
        PurePosixPath("docs/index.html"),
        "page",
        BuildFingerprint.from_text("second"),
    )

    with pytest.raises(BuildTargetCollisionError):
        BuildManifest([first, second])


def test_build_manifest_hashes_exact_page_and_asset_output_bytes(tmp_path: Path) -> None:
    asset_source = tmp_path / "app.css"
    asset_source.write_bytes(b"body { color: black; }\n")

    route = Route("/", Page("Home"))
    page = PageBuildEntry(
        route,
        PurePosixPath("index.html"),
        "<!doctype html>\n",
    )
    asset = AssetBuildEntry(
        Asset(asset_source, PurePosixPath("assets/app.css"))
    )

    manifest = build_manifest(BuildPlan([page], [asset]))

    page_entry = manifest.get(PurePosixPath("index.html"))
    asset_entry = manifest.get(PurePosixPath("assets/app.css"))

    assert page_entry is not None
    assert asset_entry is not None
    assert page_entry.kind == "page"
    assert asset_entry.kind == "asset"
    assert page_entry.fingerprint == BuildFingerprint.from_bytes(
        b"<!doctype html>\n"
    )
    assert asset_entry.fingerprint == BuildFingerprint.from_bytes(
        b"body { color: black; }\n"
    )


def test_build_manifest_is_content_based_not_target_based(tmp_path: Path) -> None:
    source = tmp_path / "same.bin"
    source.write_bytes(b"same bytes")

    first = build_manifest(
        BuildPlan(
            assets=[
                AssetBuildEntry(
                    Asset(source, PurePosixPath("assets/first.bin"))
                )
            ]
        )
    )
    second = build_manifest(
        BuildPlan(
            assets=[
                AssetBuildEntry(
                    Asset(source, PurePosixPath("assets/second.bin"))
                )
            ]
        )
    )

    assert first.entries[0].target != second.entries[0].target
    assert first.entries[0].fingerprint == second.entries[0].fingerprint


def test_build_manifest_changes_when_asset_content_changes(tmp_path: Path) -> None:
    source = tmp_path / "asset.txt"
    source.write_text("before", encoding="utf-8")
    plan = BuildPlan(
        assets=[
            AssetBuildEntry(
                Asset(source, PurePosixPath("assets/asset.txt"))
            )
        ]
    )

    before = build_manifest(plan)
    source.write_text("after", encoding="utf-8")
    after = build_manifest(plan)

    assert before.fingerprints != after.fingerprints


def test_build_manifest_performs_no_output_write(tmp_path: Path) -> None:
    source = tmp_path / "asset.txt"
    source.write_text("content", encoding="utf-8")
    output_root = tmp_path / "dist"

    build_manifest(
        BuildPlan(
            assets=[
                AssetBuildEntry(
                    Asset(source, PurePosixPath("assets/asset.txt"))
                )
            ]
        )
    )

    assert not output_root.exists()
    assert source.read_text(encoding="utf-8") == "content"


def test_build_manifest_rejects_missing_asset_source(tmp_path: Path) -> None:
    missing = tmp_path / "missing.txt"
    plan = BuildPlan(
        assets=[
            AssetBuildEntry(
                Asset(missing, PurePosixPath("assets/missing.txt"))
            )
        ]
    )

    with pytest.raises(BuildManifestSourceError, match="does not exist"):
        build_manifest(plan)


def test_build_manifest_rejects_directory_asset_source(tmp_path: Path) -> None:
    directory = tmp_path / "asset-dir"
    directory.mkdir()
    plan = BuildPlan(
        assets=[
            AssetBuildEntry(
                Asset(directory, PurePosixPath("assets/directory"))
            )
        ]
    )

    with pytest.raises(BuildManifestSourceError, match="regular file"):
        build_manifest(plan)


def test_build_manifest_requires_build_plan() -> None:
    with pytest.raises(TypeError, match="BuildPlan"):
        build_manifest(object())  # type: ignore[arg-type]
