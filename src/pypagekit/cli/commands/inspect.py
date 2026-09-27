"""Read-only project inspection command."""

from pathlib import Path
from typing import Annotated

import typer

from pypagekit.diagnostics import DiagnosticsError, ProjectInspector

from ..console import console, error_console
from ..exit_codes import EXECUTION_ERROR


def inspect_command(
    root: Annotated[
        Path,
        typer.Argument(
            help="Project directory to inspect.",
        ),
    ] = Path("."),
) -> None:
    """Describe a PyPageKit project without executing project code."""

    try:
        inspection = ProjectInspector().inspect(root)
    except DiagnosticsError as exc:
        error_console.print(f"Project inspection failed: {exc}")
        raise typer.Exit(code=EXECUTION_ERROR) from exc

    project_name = inspection.project_name or "<unknown>"

    console.print("PyPageKit Inspect")
    console.print(f"Project root: {inspection.root}")
    console.print(f"Project name: {project_name}")
    console.print(f"Python: {inspection.python_version}")
    console.print(f"PyPageKit: {inspection.pypagekit_version}")
    console.print(f"pyproject.toml: {'present' if inspection.pyproject_present else 'missing'}")
    console.print(f"site.py: {'present' if inspection.site_present else 'missing'}")
    console.print(f"Output root: {inspection.output_root}")
    console.print(f"dist/: {'present' if inspection.output_present else 'missing'}")
    console.print(f"dist/index.html: {'present' if inspection.index_present else 'missing'}")
    if inspection.metadata_error is not None:
        console.print(f"Metadata warning: {inspection.metadata_error}")


__all__ = ["inspect_command"]
