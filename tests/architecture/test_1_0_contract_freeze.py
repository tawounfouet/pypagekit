import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPOSITORY_ROOT / "API_CONTRACT_1_0.json"
GENERATOR_PATH = REPOSITORY_ROOT / "tools/api_contract_snapshot.py"


def _load_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("pypagekit_contract_snapshot", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load API contract snapshot generator.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_1_0_contract_matches_runtime_exactly() -> None:
    expected = CONTRACT_PATH.read_text(encoding="utf-8")
    actual = _load_generator().render_snapshot()

    if actual != expected:
        pytest.fail(
            "1.0 contract baseline mismatch.\n"
            "CONTRACT_SNAPSHOT_BEGIN\n"
            f"{actual}"
            "CONTRACT_SNAPSHOT_END"
        )


def test_contract_snapshot_is_canonical_json() -> None:
    content = CONTRACT_PATH.read_text(encoding="utf-8")
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


def test_contract_snapshot_targets_1_0() -> None:
    snapshot = _load_generator().build_snapshot()

    assert snapshot["schema_version"] == 1
    assert snapshot["target_release"] == "1.0.0"
    assert snapshot["active_deprecations"] == []


def test_python_cli_facade_remains_explicitly_provisional() -> None:
    snapshot = _load_generator().build_snapshot()
    provisional = snapshot["provisional_facades"]

    assert provisional == {
        "pypagekit.cli": {
            "exports": ["app", "main"],
            "frozen": False,
        }
    }
