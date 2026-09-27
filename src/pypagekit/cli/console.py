"""Centralized Rich consoles for human-facing CLI output."""

from rich.console import Console

console = Console(markup=False, highlight=False)
error_console = Console(stderr=True, markup=False, highlight=False)

__all__ = ["console", "error_console"]
