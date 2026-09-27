"""Explicit registration point for PyPageKit CLI commands."""

import typer


def register_commands(app: typer.Typer) -> None:
    """Register commands implemented by the current release.

    LOT-23 establishes the registration boundary. Concrete workflow commands
    are introduced by their dedicated roadmap lots.
    """


__all__ = ["register_commands"]
