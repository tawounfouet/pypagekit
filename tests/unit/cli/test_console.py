from rich.console import Console

from pypagekit.cli.console import console, error_console


def test_cli_consoles_are_centralized_rich_consoles() -> None:
    assert isinstance(console, Console)
    assert isinstance(error_console, Console)
    assert error_console.stderr
    assert not console.stderr
