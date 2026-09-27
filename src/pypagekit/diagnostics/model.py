"""Immutable result models for developer diagnostics."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class DiagnosticStatus(str, Enum):
    """Severity/status of one diagnostic check."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class DiagnosticCheck:
    """One deterministic developer-environment check."""

    code: str
    label: str
    status: DiagnosticStatus
    message: str


@dataclass(frozen=True, slots=True)
class DiagnosticReport:
    """Ordered result of a developer diagnostics run."""

    checks: tuple[DiagnosticCheck, ...]

    @property
    def passed(self) -> tuple[DiagnosticCheck, ...]:
        """Return checks that passed."""

        return tuple(check for check in self.checks if check.status is DiagnosticStatus.PASS)

    @property
    def warnings(self) -> tuple[DiagnosticCheck, ...]:
        """Return warning checks."""

        return tuple(
            check for check in self.checks if check.status is DiagnosticStatus.WARNING
        )

    @property
    def failures(self) -> tuple[DiagnosticCheck, ...]:
        """Return failed checks."""

        return tuple(check for check in self.checks if check.status is DiagnosticStatus.FAIL)

    @property
    def healthy(self) -> bool:
        """Whether no failing checks were found."""

        return not self.failures


@dataclass(frozen=True, slots=True)
class ProjectInspection:
    """Read-only description of a PyPageKit project root."""

    root: Path
    project_name: str | None
    python_version: str
    pypagekit_version: str
    pyproject_present: bool
    site_present: bool
    output_root: Path
    output_present: bool
    index_present: bool
    metadata_error: str | None = None


__all__ = [
    "DiagnosticCheck",
    "DiagnosticReport",
    "DiagnosticStatus",
    "ProjectInspection",
]
