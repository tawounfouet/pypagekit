import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pypagekit.cli.app import app
from pypagekit.cli.exit_codes import EXECUTION_ERROR, SUCCESS, USAGE_ERROR

runner = CliRunner()
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(output: str) -> str:
    return _ANSI_RE.sub("", output)


def test_new_help_succeeds() -> None:
    result = runner.invoke(app, ["new", "--help"])

    assert result.exit_code == SUCCESS
    output = _plain(result.output)
    assert "Create a minimal executable PyPageKit project." in output
    assert "--force" in output


def test_new_requires_target_argument() -> None:
    result = runner.invoke(app, ["new"])

    assert result.exit_code == USAGE_ERROR


def test_new_creates_project_from_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["new", "demo"])

    assert result.exit_code == SUCCESS
    assert "Created PyPageKit project 'demo' at demo" in result.stdout
    target = Path("demo")
    assert (target / ".gitignore").is_file()
    assert (target / "README.md").is_file()
    assert (target / "pyproject.toml").is_file()
    assert (target / "site.py").is_file()


def test_new_supports_current_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["new", "."])

    assert result.exit_code == SUCCESS
    assert Path("site.py").is_file()
    assert Path("pyproject.toml").is_file()


def test_new_collision_returns_execution_error_on_stderr(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    first = runner.invoke(app, ["new", "demo"])
    second = runner.invoke(app, ["new", "demo"])

    assert first.exit_code == SUCCESS
    assert second.exit_code == EXECUTION_ERROR
    assert "Project creation failed:" in second.stderr
    assert "already exists" in second.stderr


def test_new_force_replaces_managed_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    first = runner.invoke(app, ["new", "demo"])
    assert first.exit_code == SUCCESS

    site_file = Path("demo/site.py")
    site_file.write_text("custom content", encoding="utf-8")

    second = runner.invoke(app, ["new", "demo", "--force"])

    assert second.exit_code == SUCCESS
    assert "StaticSiteGenerator" in site_file.read_text(encoding="utf-8")
