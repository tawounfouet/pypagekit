import os
from dataclasses import FrozenInstanceError
from pathlib import Path, PurePosixPath

import pytest

from pypagekit import Asset, Page, Route
from pypagekit.build import (
    AssetBuildEntry,
    BuildFingerprint,
    BuildManifest,
    BuildManifestDiff,
    BuildManifestEntry,
    BuildPlan,
    PageBuildEntry,
    build_manifest,
    diff_build_manifests,
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


def test_build_manifest_rejects_asset_changed_during_hashing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "changing.bin"
    source.write_bytes(b"stable content")
    plan = BuildPlan(
        assets=[
            AssetBuildEntry(
                Asset(source, PurePosixPath("assets/changing.bin"))
            )
        ]
    )
    original_open = Path.open

    class MutatingReader:
        def __init__(self, file_object: object) -> None:
            self._file_object = file_object
            self._mutated = False

        def __enter__(self) -> "MutatingReader":
            self._file_object.__enter__()  # type: ignore[attr-defined]
            return self

        def __exit__(
            self,
            exc_type: object,
            exc_value: object,
            traceback: object,
        ) -> object:
            return self._file_object.__exit__(  # type: ignore[attr-defined]
                exc_type,
                exc_value,
                traceback,
            )

        def read(self, size: int = -1) -> bytes:
            data = self._file_object.read(size)  # type: ignore[attr-defined]
            if not self._mutated:
                self._mutated = True
                state = source.stat()
                os.utime(
                    source,
                    ns=(state.st_atime_ns, state.st_mtime_ns + 1_000_000_000),
                )
            return data

    def mutating_open(path: Path, *args: object, **kwargs: object) -> object:
        file_object = original_open(path, *args, **kwargs)  # type: ignore[arg-type]
        if path == source and args and args[0] == "rb":
            return MutatingReader(file_object)
        return file_object

    monkeypatch.setattr(Path, "open", mutating_open)

    with pytest.raises(BuildManifestSourceError, match="changed while"):
        build_manifest(plan)


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


def test_diff_build_manifests_classifies_added_changed_unchanged_and_removed() -> None:
    unchanged_previous = BuildManifestEntry(
        PurePosixPath("same.html"),
        "page",
        BuildFingerprint.from_text("same"),
    )
    changed_previous = BuildManifestEntry(
        PurePosixPath("changed.html"),
        "page",
        BuildFingerprint.from_text("before"),
    )
    removed = BuildManifestEntry(
        PurePosixPath("removed.css"),
        "asset",
        BuildFingerprint.from_bytes(b"removed"),
    )
    previous = BuildManifest(
        [unchanged_previous, changed_previous, removed]
    )

    added = BuildManifestEntry(
        PurePosixPath("added.js"),
        "asset",
        BuildFingerprint.from_bytes(b"added"),
    )
    changed_current = BuildManifestEntry(
        PurePosixPath("changed.html"),
        "page",
        BuildFingerprint.from_text("after"),
    )
    unchanged_current = BuildManifestEntry(
        PurePosixPath("same.html"),
        "page",
        BuildFingerprint.from_text("same"),
    )
    current = BuildManifest(
        [added, changed_current, unchanged_current]
    )

    diff = diff_build_manifests(previous, current)

    assert diff == BuildManifestDiff(
        added=(added,),
        changed=(changed_current,),
        unchanged=(unchanged_current,),
        removed=(removed,),
    )
    assert diff.added_targets == (PurePosixPath("added.js"),)
    assert diff.changed_targets == (PurePosixPath("changed.html"),)
    assert diff.unchanged_targets == (PurePosixPath("same.html"),)
    assert diff.removed_targets == (PurePosixPath("removed.css"),)
    assert diff.has_changes is True


def test_diff_build_manifests_treats_kind_change_as_changed() -> None:
    fingerprint = BuildFingerprint.from_bytes(b"same")
    previous = BuildManifest(
        [
            BuildManifestEntry(
                PurePosixPath("artifact"),
                "asset",
                fingerprint,
            )
        ]
    )
    current = BuildManifest(
        [
            BuildManifestEntry(
                PurePosixPath("artifact"),
                "page",
                fingerprint,
            )
        ]
    )

    diff = diff_build_manifests(previous, current)

    assert diff.changed == current.entries
    assert diff.added == ()
    assert diff.removed == ()
    assert diff.unchanged == ()


def test_diff_build_manifests_preserves_current_and_previous_declaration_order() -> None:
    first = BuildManifestEntry(
        PurePosixPath("first"),
        "page",
        BuildFingerprint.from_text("first"),
    )
    second = BuildManifestEntry(
        PurePosixPath("second"),
        "page",
        BuildFingerprint.from_text("second"),
    )
    third = BuildManifestEntry(
        PurePosixPath("third"),
        "page",
        BuildFingerprint.from_text("third"),
    )

    previous = BuildManifest([second, first])
    current = BuildManifest([third, first])

    diff = diff_build_manifests(previous, current)

    assert diff.added == (third,)
    assert diff.unchanged == (first,)
    assert diff.removed == (second,)


def test_diff_build_manifests_reports_no_changes_for_identical_manifest() -> None:
    manifest = BuildManifest(
        [
            BuildManifestEntry(
                PurePosixPath("index.html"),
                "page",
                BuildFingerprint.from_text("same"),
            )
        ]
    )

    diff = diff_build_manifests(manifest, manifest)

    assert diff.added == ()
    assert diff.changed == ()
    assert diff.removed == ()
    assert diff.unchanged == manifest.entries
    assert diff.has_changes is False


def test_diff_build_manifests_validates_inputs() -> None:
    manifest = BuildManifest()

    with pytest.raises(TypeError, match="Previous manifest"):
        diff_build_manifests(object(), manifest)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Current manifest"):
        diff_build_manifests(manifest, object())  # type: ignore[arg-type]
