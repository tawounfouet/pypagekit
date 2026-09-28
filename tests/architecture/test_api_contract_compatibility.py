import copy
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPOSITORY_ROOT / "API_CONTRACT_1_0.json"
COMPATIBILITY_PATH = REPOSITORY_ROOT / "tools/api_contract_compatibility.py"


def _load_compatibility() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "pypagekit_contract_compatibility_tests",
        COMPATIBILITY_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load API contract compatibility helper.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _baseline() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _current() -> dict[str, Any]:
    return copy.deepcopy(_baseline())


def _errors(current: dict[str, Any]) -> tuple[str, ...]:
    return _load_compatibility().compatibility_errors(_baseline(), current)


def test_exact_1_0_baseline_is_compatible_with_itself() -> None:
    assert _errors(_current()) == ()


def test_new_public_export_is_a_compatible_minor_addition() -> None:
    current = _current()
    root = current["stable_facades"]["pypagekit"]
    root["exports"].append("FutureSymbol")
    root["symbols"]["FutureSymbol"] = {
        "kind": "constant",
        "type": "str",
        "value": "future",
    }

    assert _errors(current) == ()


def test_removing_frozen_public_export_is_rejected() -> None:
    current = _current()
    root = current["stable_facades"]["pypagekit"]
    root["exports"].remove("Page")

    errors = _errors(current)

    assert any("stable_facades.pypagekit.Page was removed" in error for error in errors)


def test_optional_keyword_only_parameter_is_compatible() -> None:
    current = _current()
    symbol = current["stable_facades"]["pypagekit.domain"]["symbols"]["normalize_route_path"]
    symbol["signature"]["parameters"].append(
        {
            "name": "future_option",
            "kind": "KEYWORD_ONLY",
            "annotation": "bool",
            "required": False,
            "value": False,
        }
    )

    assert _errors(current) == ()


def test_new_required_parameter_is_rejected() -> None:
    current = _current()
    symbol = current["stable_facades"]["pypagekit.domain"]["symbols"]["normalize_route_path"]
    symbol["signature"]["parameters"].append(
        {
            "name": "required_future_option",
            "kind": "KEYWORD_ONLY",
            "annotation": "bool",
            "required": True,
        }
    )

    errors = _errors(current)

    assert any("is a new parameter but is not optional keyword-only" in error for error in errors)


def test_existing_parameter_contract_change_is_rejected() -> None:
    current = _current()
    symbol = current["stable_facades"]["pypagekit.domain"]["symbols"]["normalize_route_path"]
    parameter = symbol["signature"]["parameters"][0]
    parameter["kind"] = "KEYWORD_ONLY"

    errors = _errors(current)

    assert any(
        ".kind changed" in error or "positional parameter ordering" in error for error in errors
    )


def test_new_cli_command_is_compatible() -> None:
    current = _current()
    current["operational_contracts"]["cli"]["commands"].append("future-command")

    assert _errors(current) == ()


def test_cli_exit_code_change_is_rejected() -> None:
    current = _current()
    current["operational_contracts"]["cli"]["execution_error_exit_code"] = 42

    errors = _errors(current)

    assert any("execution_error_exit_code changed" in error for error in errors)


def test_extension_api_line_change_is_rejected() -> None:
    current = _current()
    current["operational_contracts"]["extensions"]["api_version"] = "1.0"

    errors = _errors(current)

    assert any("extensions.api_version changed" in error for error in errors)


def test_minimum_python_change_is_rejected() -> None:
    current = _current()
    current["operational_contracts"]["typing"]["minimum_python"] = "3.12"

    errors = _errors(current)

    assert any("typing.minimum_python changed" in error for error in errors)
