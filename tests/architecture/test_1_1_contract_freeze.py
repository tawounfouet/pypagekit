import importlib.util
import json
import tomllib
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_1_0_PATH = REPOSITORY_ROOT / "API_CONTRACT_1_0.json"
CONTRACT_1_1_PATH = REPOSITORY_ROOT / "API_CONTRACT_1_1.json"
GENERATOR_PATH = REPOSITORY_ROOT / "tools/api_contract_snapshot.py"
COMPATIBILITY_HELPER_PATH = REPOSITORY_ROOT / "tools/api_contract_compatibility.py"
COMPATIBILITY_POLICY_PATH = REPOSITORY_ROOT / "COMPATIBILITY.toml"


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path.name}.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_policy() -> dict[str, Any]:
    with COMPATIBILITY_POLICY_PATH.open("rb") as stream:
        return tomllib.load(stream)


def test_runtime_matches_frozen_1_1_contract_exactly() -> None:
    expected = CONTRACT_1_1_PATH.read_text(encoding="utf-8")
    actual = _load_module("pypagekit_contract_snapshot_1_1", GENERATOR_PATH).render_snapshot()

    assert actual == expected


def test_1_1_contract_snapshot_is_canonical_json() -> None:
    content = CONTRACT_1_1_PATH.read_text(encoding="utf-8")
    parsed = json.loads(content)

    assert (
        content
        == json.dumps(
            parsed,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    )


def test_1_1_contract_targets_minor_release_and_has_no_active_deprecations() -> None:
    contract = _load_json(CONTRACT_1_1_PATH)

    assert contract["schema_version"] == 1
    assert contract["target_release"] == "1.1.0"
    assert contract["active_deprecations"] == []


def test_1_1_contract_remains_compatible_with_frozen_1_0_floor() -> None:
    baseline = _load_json(CONTRACT_1_0_PATH)
    current = _load_json(CONTRACT_1_1_PATH)
    helper = _load_module("pypagekit_contract_compatibility_1_1", COMPATIBILITY_HELPER_PATH)

    errors = helper.compatibility_errors(baseline, current)

    if errors:
        pytest.fail("1.1 contract breaks the 1.0 compatibility floor:\n" + "\n".join(errors))


def test_1_1_release_freeze_policy_is_explicit() -> None:
    policy = _load_policy()
    freeze = policy["release_1_1_freeze"]

    assert freeze == {
        "frozen": True,
        "baseline": "API_CONTRACT_1_1.json",
        "target_release": "1.1.0",
        "release_candidate": "1.1.0rc1",
        "compatibility_floor": "API_CONTRACT_1_0.json",
        "extension_api_version": "0.7",
        "python_cli_facade_frozen": False,
        "shell_cli_frozen": True,
    }


def test_1_1_contract_captures_incremental_build_public_surface() -> None:
    contract = _load_json(CONTRACT_1_1_PATH)
    build = contract["stable_facades"]["pypagekit.build"]
    exceptions = contract["stable_facades"]["pypagekit.exceptions"]

    for name in (
        "BuildFingerprint",
        "BuildManifest",
        "BuildManifestDiff",
        "BuildManifestEntry",
        "IncrementalFilesystemWriteResult",
        "IncrementalStaticSiteGenerationResult",
        "build_manifest",
        "diff_build_manifests",
    ):
        assert name in build["exports"]
        assert name in build["symbols"]

    assert "IncrementalOutputDriftError" in exceptions["exports"]


def test_1_1_contract_captures_watch_and_live_reload_public_surface() -> None:
    contract = _load_json(CONTRACT_1_1_PATH)
    development = contract["stable_facades"]["pypagekit.development"]
    symbols = development["symbols"]

    for name in (
        "DevelopmentWatcher",
        "WatchChange",
        "WatchChangeBatch",
        "WatchChangeKind",
        "WatchPathKind",
        "WatchSnapshot",
        "WatchSnapshotEntry",
        "diff_watch_snapshots",
    ):
        assert name in development["exports"]
        assert name in symbols

    create_parameters = symbols["DevelopmentServer"]["members"]["create"]["signature"]["parameters"]
    live_reload = next(item for item in create_parameters if item["name"] == "live_reload")
    assert live_reload == {
        "annotation": "bool",
        "kind": "KEYWORD_ONLY",
        "name": "live_reload",
        "required": False,
        "value": False,
    }

    session_members = symbols["DevelopmentServerSession"]["members"]
    assert session_members["live_reload"]["kind"] == "property"
    assert session_members["notify_reload"]["kind"] == "method"


def test_1_1_contract_freezes_serve_watch_cli_additions() -> None:
    contract = _load_json(CONTRACT_1_1_PATH)
    cli = contract["operational_contracts"]["cli"]

    assert cli["command_arguments"]["serve"] == ["root"]
    assert cli["command_options"]["serve"] == [
        "--host",
        "--port",
        "-p",
        "--watch",
        "--entry",
        "--poll-interval",
        "--debounce-interval",
    ]


def test_python_cli_facade_remains_provisional_in_1_1_contract() -> None:
    contract = _load_json(CONTRACT_1_1_PATH)

    assert contract["provisional_facades"] == {
        "pypagekit.cli": {
            "frozen": False,
        }
    }
