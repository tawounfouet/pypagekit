"""Root Typer application for PyPageKit."""

from typing import Annotated

import typer

from pypagekit import __version__

from .commands import register_commands
from .console import console
from .exit_codes import SUCCESS

APP_HELP = "Python-first structured page and static site framework."

app = typer.Typer(
    name="pypagekit",
    help=APP_HELP,
    add_completion=True,
    suggest_commands=True,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _version_callback(value: bool | None) -> None:
    if value:
        console.print(f"PyPageKit {__version__}")
        raise typer.Exit(code=SUCCESS)


@app.callback(invoke_without_command=True)
def root(
    ctx: typer.Context,
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the installed PyPageKit version and exit.",
        ),
    ] = None,
) -> None:
    """Python-first structured page and static site framework."""

    del version
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


register_commands(app)


def main() -> None:
    """Run the installed PyPageKit CLI."""

    app(prog_name="pypagekit")


__all__ = ["APP_HELP", "app", "main"]
