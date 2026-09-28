import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPOSITORY_ROOT / "API_CONTRACT_1_0.json"
GENERATOR_PATH = REPOSITORY_ROOT / "tools/api_contract_snapshot.py"
COMPATIBILITY_PATH = REPOSITORY_ROOT / "tools/api_contract_compatibility.py"


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path.name}.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_generator() -> ModuleType:
    return _load_module("pypagekit_contract_snapshot", GENERATOR_PATH)


def _load_compatibility() -> ModuleType:
    return _load_module("pypagekit_contract_compatibility", COMPATIBILITY_PATH)


def _frozen_contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_frozen_1_0_contract_remains_compatible_with_current_runtime() -> None:
    baseline = _frozen_contract()
    current = _load_generator().build_snapshot()
    errors = _load_compatibility().compatibility_errors(baseline, current)

    if errors:
        pytest.fail("1.0 compatibility regression:\n" + "\n".join(f"- {error}" for error in errors))


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


def test_frozen_contract_targets_1_0() -> None:
    snapshot = _frozen_contract()

    assert snapshot["schema_version"] == 1
    assert snapshot["target_release"] == "1.0.0"
    assert snapshot["active_deprecations"] == []


def test_python_cli_facade_remains_explicitly_provisional() -> None:
    snapshot = _load_generator().build_snapshot()
    provisional = snapshot["provisional_facades"]

    assert provisional == {
        "pypagekit.cli": {
            "frozen": False,
        }
    }
