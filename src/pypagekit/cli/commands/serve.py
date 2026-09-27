"""Local static development server command."""

from pathlib import Path
from typing import Annotated

import typer

from pypagekit.development import (
    DevelopmentServer,
    DevelopmentServerConfig,
    DevelopmentServerError,
)

from ..console import console, error_console
from ..exit_codes import EXECUTION_ERROR


def serve_command(
    root: Annotated[
        Path,
        typer.Argument(
            help="Static output directory to serve.",
        ),
    ] = Path("dist"),
    host: Annotated[
        str,
        typer.Option(
            "--host",
            help="Hostname or IPv4 address to bind.",
        ),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option(
            "--port",
            "-p",
            min=1,
            max=65535,
            help="TCP port to bind.",
        ),
    ] = 8000,
) -> None:
    """Serve a generated static directory for local development."""

    try:
        config = DevelopmentServerConfig(
            root=root,
            host=host,
            port=port,
        )
        with DevelopmentServer().create(config) as session:
            console.print(
                f"Serving {session.info.root} at {session.info.url} "
                "(Press Ctrl+C to stop)"
            )
            try:
                session.serve_forever()
            except KeyboardInterrupt:
                console.print("Development server stopped.")
    except DevelopmentServerError as exc:
        error_console.print(f"Development server failed: {exc}")
        raise typer.Exit(code=EXECUTION_ERROR) from exc


__all__ = ["serve_command"]
