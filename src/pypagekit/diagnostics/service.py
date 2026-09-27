"""Read-only developer diagnostics and project inspection."""

import sys
import tomllib
from pathlib import Path

from pypagekit import __version__

from .exceptions import InvalidInspectionRootError
from .model import DiagnosticCheck, DiagnosticReport, DiagnosticStatus, ProjectInspection

_MIN_PYTHON = (3, 11)
_MAX_TESTED_PYTHON = (3, 14)


class DeveloperDiagnostics:
    """Evaluate whether a local PyPageKit project environment is usable."""

    def run(self, project_root: Path = Path(".")) -> DiagnosticReport:
        """Run deterministic checks without modifying the project."""

        if not isinstance(project_root, Path):
            raise TypeError("Diagnostic project_root must be a pathlib.Path.")

        pyproject = project_root / "pyproject.toml"
        site_file = project_root / "site.py"
        output_root = project_root / "dist"
        index_file = output_root / "index.html"

        return DiagnosticReport(
            checks=(
                _python_check(),
                DiagnosticCheck(
                    code="pypagekit.version",
                    label="PyPageKit version",
                    status=DiagnosticStatus.PASS,
                    message=__version__,
                ),
                _root_check(project_root),
                _regular_file_check(
                    pyproject,
                    code="project.pyproject",
                    label="pyproject.toml",
                    missing_status=DiagnosticStatus.FAIL,
                ),
                _metadata_check(pyproject),
                _regular_file_check(
                    site_file,
                    code="project.site",
                    label="site.py",
                    missing_status=DiagnosticStatus.FAIL,
                ),
                _directory_check(
                    output_root,
                    code="output.directory",
                    label="dist/",
                    missing_status=DiagnosticStatus.WARNING,
                ),
                _regular_file_check(
                    index_file,
                    code="output.index",
                    label="dist/index.html",
                    missing_status=DiagnosticStatus.WARNING,
                ),
            )
        )


class ProjectInspector:
    """Describe a project root without loading or executing project code."""

    def inspect(self, project_root: Path = Path(".")) -> ProjectInspection:
        """Return filesystem/package facts for a project root."""

        if not isinstance(project_root, Path):
            raise TypeError("Inspection project_root must be a pathlib.Path.")
        if project_root.is_symlink():
            raise InvalidInspectionRootError(
                f"Inspection root '{project_root}' must not be a symlink."
            )
        if not project_root.exists():
            raise InvalidInspectionRootError(f"Inspection root '{project_root}' does not exist.")
        if not project_root.is_dir():
            raise InvalidInspectionRootError(
                f"Inspection root '{project_root}' must be a directory."
            )

        pyproject = project_root / "pyproject.toml"
        site_file = project_root / "site.py"
        output_root = project_root / "dist"
        index_file = output_root / "index.html"

        project_name: str | None = None
        metadata_error: str | None = None
        if pyproject.is_file() and not pyproject.is_symlink():
            project_name, metadata_error = _read_project_name(pyproject)

        return ProjectInspection(
            root=project_root.absolute(),
            project_name=project_name,
            python_version=_python_version(),
            pypagekit_version=__version__,
            pyproject_present=pyproject.is_file() and not pyproject.is_symlink(),
            site_present=site_file.is_file() and not site_file.is_symlink(),
            output_root=output_root.absolute(),
            output_present=output_root.is_dir() and not output_root.is_symlink(),
            index_present=index_file.is_file() and not index_file.is_symlink(),
            metadata_error=metadata_error,
        )


def _python_version() -> str:
    return ".".join(str(part) for part in sys.version_info[:3])


def _python_check() -> DiagnosticCheck:
    current = (sys.version_info.major, sys.version_info.minor)
    version = _python_version()

    if sys.version_info.major != 3 or current < _MIN_PYTHON:
        return DiagnosticCheck(
            code="python.version",
            label="Python version",
            status=DiagnosticStatus.FAIL,
            message=f"{version} is unsupported; Python 3.11+ is required.",
        )
    if current > _MAX_TESTED_PYTHON:
        return DiagnosticCheck(
            code="python.version",
            label="Python version",
            status=DiagnosticStatus.WARNING,
            message=f"{version} is newer than the currently tested Python 3.14 line.",
        )
    return DiagnosticCheck(
        code="python.version",
        label="Python version",
        status=DiagnosticStatus.PASS,
        message=f"{version} is supported.",
    )


def _root_check(path: Path) -> DiagnosticCheck:
    if path.is_symlink():
        return DiagnosticCheck(
            code="project.root",
            label="Project root",
            status=DiagnosticStatus.FAIL,
            message=f"{path} is a symlink.",
        )
    if not path.exists():
        return DiagnosticCheck(
            code="project.root",
            label="Project root",
            status=DiagnosticStatus.FAIL,
            message=f"{path} does not exist.",
        )
    if not path.is_dir():
        return DiagnosticCheck(
            code="project.root",
            label="Project root",
            status=DiagnosticStatus.FAIL,
            message=f"{path} is not a directory.",
        )
    return DiagnosticCheck(
        code="project.root",
        label="Project root",
        status=DiagnosticStatus.PASS,
        message=str(path.absolute()),
    )


def _regular_file_check(
    path: Path,
    *,
    code: str,
    label: str,
    missing_status: DiagnosticStatus,
) -> DiagnosticCheck:
    if path.is_symlink():
        return DiagnosticCheck(code, label, DiagnosticStatus.FAIL, f"{path} is a symlink.")
    if not path.exists():
        return DiagnosticCheck(code, label, missing_status, f"{path} is missing.")
    if not path.is_file():
        return DiagnosticCheck(
            code,
            label,
            DiagnosticStatus.FAIL,
            f"{path} is not a regular file.",
        )
    return DiagnosticCheck(code, label, DiagnosticStatus.PASS, f"{path} is present.")


def _directory_check(
    path: Path,
    *,
    code: str,
    label: str,
    missing_status: DiagnosticStatus,
) -> DiagnosticCheck:
    if path.is_symlink():
        return DiagnosticCheck(code, label, DiagnosticStatus.FAIL, f"{path} is a symlink.")
    if not path.exists():
        return DiagnosticCheck(code, label, missing_status, f"{path} is missing.")
    if not path.is_dir():
        return DiagnosticCheck(
            code,
            label,
            DiagnosticStatus.FAIL,
            f"{path} is not a directory.",
        )
    return DiagnosticCheck(code, label, DiagnosticStatus.PASS, f"{path} is present.")


def _metadata_check(pyproject: Path) -> DiagnosticCheck:
    if not pyproject.exists():
        return DiagnosticCheck(
            "project.metadata",
            "Project metadata",
            DiagnosticStatus.FAIL,
            "Cannot inspect project metadata without pyproject.toml.",
        )
    if pyproject.is_symlink() or not pyproject.is_file():
        return DiagnosticCheck(
            "project.metadata",
            "Project metadata",
            DiagnosticStatus.FAIL,
            "Project metadata source must be a regular pyproject.toml file.",
        )

    name, error = _read_project_name(pyproject)
    if error is not None:
        return DiagnosticCheck(
            "project.metadata",
            "Project metadata",
            DiagnosticStatus.FAIL,
            error,
        )
    if name is None:
        return DiagnosticCheck(
            "project.metadata",
            "Project metadata",
            DiagnosticStatus.FAIL,
            "pyproject.toml does not define a non-empty [project].name.",
        )
    return DiagnosticCheck(
        "project.metadata",
        "Project metadata",
        DiagnosticStatus.PASS,
        f"Project name: {name}",
    )


def _read_project_name(pyproject: Path) -> tuple[str | None, str | None]:
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        return None, f"Unable to read project metadata: {exc}"

    project = data.get("project")
    if not isinstance(project, dict):
        return None, None

    name = project.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip(), None
    return None, None


__all__ = [
    "DeveloperDiagnostics",
    "ProjectInspector",
]
