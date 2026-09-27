"""Immutable project scaffolding plan models."""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .exceptions import ProjectPathConflictError


@dataclass(frozen=True, slots=True)
class ProjectFile:
    """One UTF-8 text file declared by a project scaffold."""

    target: PurePosixPath
    content: str

    def __post_init__(self) -> None:
        if not isinstance(self.target, PurePosixPath) or isinstance(self.target, Path):
            raise TypeError("Project file target must be a pathlib.PurePosixPath.")
        if self.target.is_absolute() or self.target == PurePosixPath("."):
            raise ProjectPathConflictError(
                "Project file target must be non-empty and relative."
            )
        if any(part in {".", ".."} for part in self.target.parts):
            raise ProjectPathConflictError(
                "Project file target must not contain traversal segments."
            )
        if not isinstance(self.content, str):
            raise TypeError("Project file content must be a string.")


@dataclass(frozen=True, slots=True, init=False)
class ProjectPlan:
    """Immutable deterministic plan for one generated PyPageKit project."""

    target_root: Path
    project_name: str
    files: tuple[ProjectFile, ...]

    def __init__(
        self,
        target_root: Path,
        project_name: str,
        files: Iterable[ProjectFile],
    ) -> None:
        if not isinstance(target_root, Path):
            raise TypeError("Project plan target_root must be a pathlib.Path.")
        if not isinstance(project_name, str):
            raise TypeError("Project plan project_name must be a string.")

        normalized_files = tuple(files)
        invalid_files = [
            project_file
            for project_file in normalized_files
            if not isinstance(project_file, ProjectFile)
        ]
        if invalid_files:
            invalid_type = type(invalid_files[0]).__name__
            raise TypeError(
                "Project plan files must contain only ProjectFile objects; "
                f"got {invalid_type}."
            )

        seen_targets: set[PurePosixPath] = set()
        for project_file in normalized_files:
            if project_file.target in seen_targets:
                raise ProjectPathConflictError(
                    f"Project file target '{project_file.target.as_posix()}' "
                    "appears more than once."
                )
            seen_targets.add(project_file.target)

        object.__setattr__(self, "target_root", target_root)
        object.__setattr__(self, "project_name", project_name)
        object.__setattr__(self, "files", normalized_files)

    @property
    def targets(self) -> tuple[PurePosixPath, ...]:
        """Return planned project-relative file targets in declaration order."""

        return tuple(project_file.target for project_file in self.files)


@dataclass(frozen=True, slots=True)
class ProjectScaffoldResult:
    """Immutable result of materializing a project scaffold."""

    plan: ProjectPlan
    files: tuple[Path, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.plan, ProjectPlan):
            raise TypeError("Project scaffold result plan must be a ProjectPlan.")

    @property
    def target_root(self) -> Path:
        """Return the generated project root."""

        return self.plan.target_root

    @property
    def project_name(self) -> str:
        """Return the normalized generated project name."""

        return self.plan.project_name


__all__ = [
    "ProjectFile",
    "ProjectPlan",
    "ProjectScaffoldResult",
]
