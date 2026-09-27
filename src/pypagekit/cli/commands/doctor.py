"""Developer diagnostics command."""

from pathlib import Path
from typing import Annotated

import typer

from pypagekit.diagnostics import DeveloperDiagnostics, DiagnosticStatus

from ..console import console
from ..exit_codes import EXECUTION_ERROR

_MARKERS = {
    DiagnosticStatus.PASS: "✓",
    DiagnosticStatus.WARNING: "!",
    DiagnosticStatus.FAIL: "✗",
}


def doctor_command(
    root: Annotated[
        Path,
        typer.Argument(
            help="Project directory to diagnose.",
        ),
    ] = Path("."),
) -> None:
    """Check whether a local PyPageKit project environment is usable."""

    report = DeveloperDiagnostics().run(root)

    console.print("PyPageKit Doctor")
    for check in report.checks:
        console.print(
            f"{_MARKERS[check.status]} [{check.status.value}] {check.label}: {check.message}"
        )

    console.print(
        f"Result: {len(report.passed)} passed, "
        f"{len(report.warnings)} warning(s), {len(report.failures)} failure(s)."
    )
    if not report.healthy:
        raise typer.Exit(code=EXECUTION_ERROR)


__all__ = ["doctor_command"]
