import re

from typer.testing import CliRunner

from pypagekit import __version__
from pypagekit.cli.app import APP_HELP, app
from pypagekit.cli.exit_codes import SUCCESS, USAGE_ERROR

runner = CliRunner()
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(output: str) -> str:
    return _ANSI_RE.sub("", output)


def test_help_succeeds_and_describes_pypagekit() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == SUCCESS
    output = _plain(result.output)
    assert APP_HELP in output
    assert "--version" in output
    assert "--help" in output


def test_short_help_alias_succeeds() -> None:
    result = runner.invoke(app, ["-h"])

    assert result.exit_code == SUCCESS
    assert APP_HELP in _plain(result.output)


def test_bare_invocation_shows_help_and_succeeds() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == SUCCESS
    output = _plain(result.output)
    assert APP_HELP in output
    assert "--version" in output


def test_version_succeeds_on_stdout() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == SUCCESS
    assert result.stdout.strip() == f"PyPageKit {__version__}"
    assert result.stderr == ""


def test_unknown_option_is_usage_error() -> None:
    result = runner.invoke(app, ["--does-not-exist"])

    assert result.exit_code == USAGE_ERROR
    assert "No such option" in result.output


def test_unknown_command_is_usage_error() -> None:
    result = runner.invoke(app, ["not-a-command"])

    assert result.exit_code == USAGE_ERROR
    assert "not-a-command" in result.output


def test_cli_help_advertises_only_implemented_workflow_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == SUCCESS
    output = _plain(result.output)
    assert " new " in output
    for command in ("build", "serve", "inspect", "doctor"):
        assert f" {command} " not in output
