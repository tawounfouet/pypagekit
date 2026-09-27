import importlib
import tomllib
from pathlib import Path

from pypagekit import __version__
from pypagekit.cli.exit_codes import EXECUTION_ERROR, SUCCESS, USAGE_ERROR
from pypagekit.extensions import (
    BUILD_PLANNER_ENTRY_POINT_GROUP,
    BUILD_PLANNER_EXTENSION_ID,
    BUILTIN_COMPONENTS_EXTENSION_ID,
    COMPONENT_ENTRY_POINT_GROUP,
    HTML_RENDERER_EXTENSION_ID,
    PYPAGEKIT_EXTENSION_API_VERSION,
    RENDERER_ENTRY_POINT_GROUP,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = REPOSITORY_ROOT / "PUBLIC_API.toml"
PYPROJECT_PATH = REPOSITORY_ROOT / "pyproject.toml"

EXPECTED_FACADES = {
    "pypagekit",
    "pypagekit.build",
    "pypagekit.cli",
    "pypagekit.components",
    "pypagekit.development",
    "pypagekit.diagnostics",
    "pypagekit.domain",
    "pypagekit.exceptions",
    "pypagekit.extensions",
    "pypagekit.project",
    "pypagekit.rendering",
}

ALLOWED_MODULE_CLASSIFICATIONS = {
    "stable",
    "provisional_public",
}


def _inventory() -> dict[str, object]:
    with INVENTORY_PATH.open("rb") as inventory_file:
        return tomllib.load(inventory_file)


def _pyproject() -> dict[str, object]:
    with PYPROJECT_PATH.open("rb") as pyproject_file:
        return tomllib.load(pyproject_file)


def test_inventory_tracks_current_package_version() -> None:
    inventory = _inventory()

    assert inventory["package_version"] == __version__


def test_inventory_covers_exact_public_facades() -> None:
    inventory = _inventory()
    modules = inventory["modules"]
    assert isinstance(modules, list)

    names = {module["name"] for module in modules}

    assert names == EXPECTED_FACADES


def test_inventory_matches_runtime_all_exports_exactly() -> None:
    inventory = _inventory()
    modules = inventory["modules"]
    assert isinstance(modules, list)

    for module_inventory in modules:
        module_name = module_inventory["name"]
        classification = module_inventory["classification"]
        expected_exports = module_inventory["exports"]

        assert isinstance(module_name, str)
        assert classification in ALLOWED_MODULE_CLASSIFICATIONS
        assert isinstance(expected_exports, list)
        assert len(expected_exports) == len(set(expected_exports))

        module = importlib.import_module(module_name)
        runtime_exports = getattr(module, "__all__", None)

        assert runtime_exports is not None, module_name
        assert list(runtime_exports) == expected_exports, module_name
        for export_name in expected_exports:
            assert hasattr(module, export_name), f"{module_name}.{export_name}"


def test_frozen_stable_facades_are_explicit() -> None:
    inventory = _inventory()
    modules = inventory["modules"]
    assert isinstance(modules, list)

    classifications = {module["name"]: module["classification"] for module in modules}

    assert classifications["pypagekit"] == "stable"
    assert classifications["pypagekit.domain"] == "stable"
    assert classifications["pypagekit.components"] == "stable"
    assert classifications["pypagekit.rendering"] == "stable"
    assert classifications["pypagekit.build"] == "stable"
    assert classifications["pypagekit.project"] == "stable"
    assert classifications["pypagekit.development"] == "stable"
    assert classifications["pypagekit.diagnostics"] == "stable"
    assert classifications["pypagekit.extensions"] == "stable"
    assert classifications["pypagekit.exceptions"] == "stable"
    assert classifications["pypagekit.cli"] == "provisional_public"


def test_internal_examples_are_not_public_facades() -> None:
    inventory = _inventory()
    modules = inventory["modules"]
    internal_policy = inventory["internal_policy"]
    assert isinstance(modules, list)
    assert isinstance(internal_policy, dict)

    public_modules = {module["name"] for module in modules}
    examples = internal_policy["examples"]
    assert isinstance(examples, list)

    assert all(example not in public_modules for example in examples)
    assert internal_policy["classification"] == "internal"


def test_cli_operational_contract_matches_package_metadata() -> None:
    inventory = _inventory()
    pyproject = _pyproject()
    cli = inventory["cli"]
    assert isinstance(cli, dict)

    project = pyproject["project"]
    assert isinstance(project, dict)
    scripts = project["scripts"]
    assert isinstance(scripts, dict)

    assert cli["classification"] == "operational_contract"
    assert cli["console_script"] == "pypagekit"
    assert cli["module_entry"] == "python -m pypagekit"
    assert scripts["pypagekit"] == "pypagekit.cli.app:main"
    assert cli["commands"] == ["doctor", "inspect", "new", "serve"]
    assert cli["root_options"] == ["--help", "--version"]
    assert cli["success_exit_code"] == SUCCESS
    assert cli["execution_error_exit_code"] == EXECUTION_ERROR
    assert cli["usage_error_exit_code"] == USAGE_ERROR


def test_extension_operational_contract_matches_runtime_constants() -> None:
    inventory = _inventory()
    extensions = inventory["extensions"]
    assert isinstance(extensions, dict)

    assert extensions["classification"] == "operational_contract"
    assert extensions["api_version"] == PYPAGEKIT_EXTENSION_API_VERSION
    assert extensions["renderer_entry_point_group"] == RENDERER_ENTRY_POINT_GROUP
    assert extensions["build_planner_entry_point_group"] == BUILD_PLANNER_ENTRY_POINT_GROUP
    assert extensions["component_entry_point_group"] == COMPONENT_ENTRY_POINT_GROUP
    assert extensions["builtin_renderer_id"] == HTML_RENDERER_EXTENSION_ID
    assert extensions["builtin_build_planner_id"] == BUILD_PLANNER_EXTENSION_ID
    assert extensions["builtin_components_id"] == BUILTIN_COMPONENTS_EXTENSION_ID


def test_typing_operational_contract_matches_package_metadata() -> None:
    inventory = _inventory()
    pyproject = _pyproject()
    typing = inventory["typing"]
    assert isinstance(typing, dict)

    project = pyproject["project"]
    assert isinstance(project, dict)

    assert typing["classification"] == "operational_contract"
    assert typing["py_typed"] is True
    assert (REPOSITORY_ROOT / "src/pypagekit/py.typed").is_file()
    assert typing["minimum_python"] == "3.11"
    assert project["requires-python"] == ">=3.11"
