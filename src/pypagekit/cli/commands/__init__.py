"""Explicit registration point for PyPageKit CLI commands."""

import typer

from .new import new_command


def register_commands(app: typer.Typer) -> None:
    """Register commands implemented by the current release."""

    app.command(
        name="new",
        help="Create a minimal executable PyPageKit project.",
    )(new_command)


__all__ = ["register_commands"]
