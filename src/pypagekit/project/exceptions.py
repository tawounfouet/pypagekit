"""Project scaffolding exceptions."""

from pypagekit.exceptions import PyPageKitError


class ProjectError(PyPageKitError):
    """Base exception for PyPageKit project operations."""


class ProjectScaffoldingError(ProjectError):
    """Base exception for project scaffolding failures."""


class InvalidProjectNameError(ProjectScaffoldingError):
    """Raised when a project name cannot be normalized safely."""


class InvalidProjectTargetError(ProjectScaffoldingError):
    """Raised when a project target root is unusable."""


class ExistingProjectFileError(ProjectScaffoldingError):
    """Raised when a generated file already exists and force is disabled."""


class ProjectPathConflictError(ProjectScaffoldingError):
    """Raised when existing filesystem structure conflicts with the scaffold."""


class ProjectSymlinkError(ProjectScaffoldingError):
    """Raised when a scaffold would traverse or replace a symlink."""


class ProjectScaffoldWriteError(ProjectScaffoldingError):
    """Raised when project materialization fails after successful preflight."""


__all__ = [
    "ExistingProjectFileError",
    "InvalidProjectNameError",
    "InvalidProjectTargetError",
    "ProjectError",
    "ProjectPathConflictError",
    "ProjectScaffoldWriteError",
    "ProjectScaffoldingError",
    "ProjectSymlinkError",
]
