"""Explicit registration point for PyPageKit CLI commands."""

import typer

from .new import new_command
from .serve import serve_command


def register_commands(app: typer.Typer) -> None:
    """Register commands implemented by the current release."""

    app.command(
        name="new",
        help="Create a minimal executable PyPageKit project.",
    )(new_command)
    app.command(
        name="serve",
        help="Serve generated static output for local development.",
    )(serve_command)


__all__ = ["register_commands"]
