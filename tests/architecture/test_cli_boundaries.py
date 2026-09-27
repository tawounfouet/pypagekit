import ast
import subprocess
import sys
from pathlib import Path

CORE_PACKAGES = (
    "domain",
    "components",
    "rendering",
    "build",
    "development",
    "project",
)
FORBIDDEN_CLI_DEPENDENCIES = {"typer", "rich"}


def test_core_packages_do_not_import_cli_dependencies() -> None:
    package_root = Path(__file__).parents[2] / "src" / "pypagekit"

    violations: list[str] = []
    for package_name in CORE_PACKAGES:
        for source_file in (package_root / package_name).rglob("*.py"):
            tree = ast.parse(source_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                imported_roots: set[str] = set()
                if isinstance(node, ast.Import):
                    imported_roots.update(
                        alias.name.split(".", maxsplit=1)[0] for alias in node.names
                    )
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_roots.add(node.module.split(".", maxsplit=1)[0])

                forbidden = imported_roots & FORBIDDEN_CLI_DEPENDENCIES
                if forbidden:
                    names = ", ".join(sorted(forbidden))
                    violations.append(f"{source_file}: {names}")

    assert violations == []


def test_importing_root_package_does_not_load_cli_dependencies() -> None:
    script = (
        "import sys; "
        "import pypagekit; "
        "assert 'typer' not in sys.modules; "
        "assert 'rich' not in sys.modules"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
