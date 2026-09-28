"""Plan and materialize minimal PyPageKit projects."""

import re
from pathlib import Path, PurePosixPath

from pypagekit import __version__
from pypagekit._filesystem_transaction import (
    FilesystemTransaction,
    FilesystemTransactionRollbackError,
)

from .exceptions import (
    ExistingProjectFileError,
    InvalidProjectNameError,
    InvalidProjectTargetError,
    ProjectPathConflictError,
    ProjectScaffoldRollbackError,
    ProjectScaffoldWriteError,
    ProjectSymlinkError,
)
from .model import ProjectFile, ProjectPlan, ProjectScaffoldResult

_INVALID_PROJECT_NAME_CHARS_RE = re.compile(r"[^a-z0-9]+")
_VERSION_PREFIX_RE = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)")


def normalize_project_name(value: str) -> str:
    """Normalize a filesystem-derived value into a distribution-style name."""

    if not isinstance(value, str):
        raise TypeError("Project name must be a string.")

    normalized = _INVALID_PROJECT_NAME_CHARS_RE.sub("-", value.strip().lower()).strip("-")
    if not normalized:
        raise InvalidProjectNameError(
            "Project name must contain at least one ASCII letter or digit."
        )
    return normalized


def pypagekit_requirement() -> str:
    """Return the compatible PyPageKit requirement for generated projects."""

    match = _VERSION_PREFIX_RE.match(__version__)
    if match is None:
        raise RuntimeError(f"Unsupported PyPageKit version format: {__version__!r}.")

    major = int(match.group("major"))
    minor = int(match.group("minor"))
    return f"pypagekit>={__version__},<{major}.{minor + 1}"


class ProjectScaffolder:
    """Create deterministic minimal PyPageKit project scaffolds."""

    def plan(
        self,
        target_root: Path,
        *,
        project_name: str | None = None,
    ) -> ProjectPlan:
        """Create a project plan without filesystem I/O."""

        if not isinstance(target_root, Path):
            raise TypeError("Project scaffold target_root must be a pathlib.Path.")

        source_name = project_name
        if source_name is None:
            if target_root.name:
                source_name = target_root.name
            elif target_root == Path("."):
                source_name = Path.cwd().name
            else:
                raise InvalidProjectNameError(
                    "Project name cannot be derived from the target root."
                )
        normalized_name = normalize_project_name(source_name)

        files = (
            ProjectFile(PurePosixPath(".gitignore"), _gitignore_content()),
            ProjectFile(
                PurePosixPath("README.md"),
                _readme_content(normalized_name),
            ),
            ProjectFile(
                PurePosixPath("pyproject.toml"),
                _pyproject_content(normalized_name),
            ),
            ProjectFile(PurePosixPath("site.py"), _site_content()),
        )

        return ProjectPlan(
            target_root=target_root,
            project_name=normalized_name,
            files=files,
        )

    def write(
        self,
        plan: ProjectPlan,
        *,
        force: bool = False,
    ) -> ProjectScaffoldResult:
        """Materialize a precomputed project plan."""

        if not isinstance(plan, ProjectPlan):
            raise TypeError("Project scaffolder plan must be a ProjectPlan.")
        if not isinstance(force, bool):
            raise TypeError("Project scaffolder force flag must be a bool.")

        self._preflight(plan, force=force)

        transaction = FilesystemTransaction()
        written_files: list[Path] = []

        try:
            transaction.ensure_directory(plan.target_root)
            for project_file in plan.files:
                destination = _destination(plan.target_root, project_file.target)
                transaction.prepare_file(
                    destination,
                    backup_existing=force,
                )
                mode = "w" if force else "x"
                with destination.open(
                    mode,
                    encoding="utf-8",
                    newline="",
                ) as output_file:
                    output_file.write(project_file.content)
                written_files.append(destination)

            transaction.commit()
        except Exception as exc:
            try:
                transaction.rollback()
            except FilesystemTransactionRollbackError as rollback_exc:
                raise ProjectScaffoldRollbackError(
                    f"Project rollback failed under '{plan.target_root}' after "
                    f"{type(exc).__name__}."
                ) from rollback_exc

            raise ProjectScaffoldWriteError(
                f"Project scaffolding failed under '{plan.target_root}'."
            ) from exc

        return ProjectScaffoldResult(
            plan=plan,
            files=tuple(written_files),
        )

    def scaffold(
        self,
        target_root: Path,
        *,
        project_name: str | None = None,
        force: bool = False,
    ) -> ProjectScaffoldResult:
        """Plan and materialize a new PyPageKit project."""

        plan = self.plan(target_root, project_name=project_name)
        return self.write(plan, force=force)

    def _preflight(self, plan: ProjectPlan, *, force: bool) -> None:
        target_root = plan.target_root

        _validate_target_root_symlinks(target_root)
        if target_root.exists() and not target_root.is_dir():
            raise InvalidProjectTargetError(
                f"Project target root '{target_root}' must be a directory."
            )

        for project_file in plan.files:
            destination = _destination(target_root, project_file.target)
            _validate_destination(
                target_root,
                destination,
                force=force,
            )


def _validate_target_root_symlinks(target_root: Path) -> None:
    cursor = target_root
    while True:
        if cursor.is_symlink():
            raise ProjectSymlinkError(f"Project target path '{cursor}' must not be a symlink.")
        if cursor == cursor.parent:
            break
        cursor = cursor.parent


def _destination(target_root: Path, target: PurePosixPath) -> Path:
    return target_root.joinpath(*target.parts)


def _validate_destination(
    target_root: Path,
    destination: Path,
    *,
    force: bool,
) -> None:
    relative = destination.relative_to(target_root)
    cursor = target_root

    for part in relative.parts[:-1]:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ProjectSymlinkError(f"Project path ancestor '{cursor}' must not be a symlink.")
        if cursor.exists() and not cursor.is_dir():
            raise ProjectPathConflictError(f"Project path ancestor '{cursor}' is not a directory.")

    if destination.is_symlink():
        raise ProjectSymlinkError(f"Project target '{destination}' must not be a symlink.")

    if destination.exists():
        if destination.is_dir():
            raise ProjectPathConflictError(
                f"Project target '{destination}' is an existing directory."
            )
        if force and destination.stat(follow_symlinks=False).st_nlink > 1:
            raise ProjectPathConflictError(
                f"Project target '{destination}' must not be a hard-linked file."
            )
        if not force:
            raise ExistingProjectFileError(f"Project target '{destination}' already exists.")


def _gitignore_content() -> str:
    return """.venv/
__pycache__/
*.py[cod]
dist/
"""


def _readme_content(project_name: str) -> str:
    return f"""# {project_name}

Generated with PyPageKit.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Build

```bash
python site.py
```

Generated output is written to `dist/`.

## Preview

```bash
pypagekit serve
```

The development server serves `dist/` at `http://127.0.0.1:8000` by default.

For automatic rebuilds and browser live reload while editing the project:

```bash
pypagekit serve --watch
```

Watch mode executes the project entry in a fresh Python subprocess to obtain the module-level
`site` value, ignores the generated `dist/` tree, applies incremental output updates, and reloads
connected browser pages only after a successful rebuild.

## Diagnostics

```bash
pypagekit doctor
pypagekit inspect
```

`doctor` checks whether the local project environment is usable. `inspect` reports
project facts without executing `site.py`.
"""


def _pyproject_content(project_name: str) -> str:
    requirement = pypagekit_requirement()
    return f"""[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "{requirement}",
]

[tool.setuptools]
py-modules = []
"""


def _site_content() -> str:
    return """from pathlib import Path

from pypagekit import Page, Paragraph, Route, Site
from pypagekit.build import StaticSiteGenerator


site = Site(
    [
        Route(
            "/",
            Page(
                "Home",
                [
                    Paragraph("Welcome to your PyPageKit site."),
                ],
            ),
        )
    ]
)


def main() -> None:
    result = StaticSiteGenerator().generate(
        site,
        Path("dist"),
        overwrite=True,
    )
    print(f"Generated {len(result.files)} file(s) in {result.output_root}")


if __name__ == "__main__":
    main()
"""


__all__ = [
    "ProjectScaffolder",
    "normalize_project_name",
    "pypagekit_requirement",
]
