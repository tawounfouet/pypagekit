"""Project-level application services for PyPageKit."""

from .exceptions import (
    ExistingProjectFileError,
    InvalidProjectNameError,
    InvalidProjectTargetError,
    ProjectError,
    ProjectPathConflictError,
    ProjectScaffoldingError,
    ProjectScaffoldWriteError,
    ProjectSymlinkError,
)
from .model import ProjectFile, ProjectPlan, ProjectScaffoldResult
from .scaffolder import ProjectScaffolder, normalize_project_name, pypagekit_requirement

__all__ = [
    "ExistingProjectFileError",
    "InvalidProjectNameError",
    "InvalidProjectTargetError",
    "ProjectError",
    "ProjectFile",
    "ProjectPathConflictError",
    "ProjectPlan",
    "ProjectScaffolder",
    "ProjectScaffoldingError",
    "ProjectScaffoldResult",
    "ProjectScaffoldWriteError",
    "ProjectSymlinkError",
    "normalize_project_name",
    "pypagekit_requirement",
]
