"""Project scaffolding command."""

from pathlib import Path
from typing import Annotated

import typer

from pypagekit.project import ProjectScaffolder, ProjectScaffoldingError

from ..console import console, error_console
from ..exit_codes import EXECUTION_ERROR


def new_command(
    target: Annotated[
        Path,
        typer.Argument(
            help="Directory to create or populate with a minimal PyPageKit project.",
        ),
    ],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Replace scaffold-managed regular files that already exist.",
        ),
    ] = False,
) -> None:
    """Create a minimal executable PyPageKit project."""

    try:
        result = ProjectScaffolder().scaffold(
            target,
            force=force,
        )
    except ProjectScaffoldingError as exc:
        error_console.print(f"Project creation failed: {exc}")
        raise typer.Exit(code=EXECUTION_ERROR) from exc

    console.print(
        f"Created PyPageKit project '{result.project_name}' at {result.target_root}"
    )
    for created_file in result.files:
        console.print(f"  {created_file.relative_to(result.target_root)}")


__all__ = ["new_command"]
