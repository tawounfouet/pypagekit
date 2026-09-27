import tomllib
from pathlib import Path

from pypagekit import __version__

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_API_PATH = REPOSITORY_ROOT / "PUBLIC_API.toml"
COMPATIBILITY_PATH = REPOSITORY_ROOT / "COMPATIBILITY.toml"
DEPRECATIONS_PATH = REPOSITORY_ROOT / "DEPRECATIONS.toml"
MIGRATION_PATH = REPOSITORY_ROOT / "MIGRATION_0_9_TO_1_0.md"

REQUIRED_DEPRECATION_FIELDS = {
    "id",
    "kind",
    "public_path",
    "since",
    "replacement",
    "removal",
}


def _load(path: Path) -> dict[str, object]:
    with path.open("rb") as source:
        return tomllib.load(source)


def test_compatibility_artifacts_track_current_package_version() -> None:
    assert _load(PUBLIC_API_PATH)["package_version"] == __version__
    assert _load(COMPATIBILITY_PATH)["package_version"] == __version__
    assert _load(DEPRECATIONS_PATH)["package_version"] == __version__


def test_compatibility_policy_forbids_silent_removal() -> None:
    policy = _load(COMPATIBILITY_PATH)
    deprecation = policy["deprecation"]
    migration = policy["migration"]
    assert isinstance(deprecation, dict)
    assert isinstance(migration, dict)

    assert deprecation["warning_category"] == "DeprecationWarning"
    assert deprecation["silent_removal_allowed"] is False
    assert deprecation["post_1_0_minimum"] == (
        "A stable API deprecated in 1.x remains available until the next major release."
    )
    assert migration["required_for_breaking_change"] is True
    assert migration["changelog_required"] is True


def test_compatibility_policy_classifies_known_breaking_changes() -> None:
    policy = _load(COMPATIBILITY_PATH)
    stable = policy["stable_candidate"]
    assert isinstance(stable, dict)

    breaking = stable["breaking_changes"]
    compatible = stable["compatible_changes"]
    assert isinstance(breaking, list)
    assert isinstance(compatible, list)

    assert "remove or rename public facade export" in breaking
    assert "move canonical public import path without compatibility alias" in breaking
    assert "remove or rename CLI command, option, or exit-code meaning" in breaking
    assert "add new public symbol" in compatible
    assert "add optional keyword-only parameter with backward-compatible default" in compatible


def test_deprecation_registry_has_unique_complete_entries() -> None:
    registry = _load(DEPRECATIONS_PATH)
    entries = registry["deprecations"]
    assert isinstance(entries, list)

    ids: set[str] = set()
    for entry in entries:
        assert isinstance(entry, dict)
        assert REQUIRED_DEPRECATION_FIELDS <= entry.keys()
        deprecation_id = entry["id"]
        assert isinstance(deprecation_id, str)
        assert deprecation_id not in ids
        ids.add(deprecation_id)

        for field in REQUIRED_DEPRECATION_FIELDS:
            value = entry[field]
            assert isinstance(value, str)
            assert value.strip()


def test_lot_35_starts_with_no_active_public_deprecations() -> None:
    registry = _load(DEPRECATIONS_PATH)

    assert registry["deprecations"] == []


def test_migration_guide_exists_and_references_release_candidate_path() -> None:
    content = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "0.9.0b1" in content
    assert "0.9.0rc1" in content
    assert "1.0.0" in content
    assert "DeprecationWarning" in content
    assert "PUBLIC_API.md" in content
