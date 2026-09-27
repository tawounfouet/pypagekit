import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pypagekit.cli.app import app
from pypagekit.cli.exit_codes import EXECUTION_ERROR, SUCCESS

runner = CliRunner()
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(output: str) -> str:
    return _ANSI_RE.sub("", output)


def _write_project(root: Path, *, with_output: bool) -> None:
    root.mkdir()
    (root / "pyproject.toml").write_text(
        '[project]\nname = "doctor-demo"\n',
        encoding="utf-8",
    )
    (root / "site.py").write_text("# no execution required\n", encoding="utf-8")
    if with_output:
        output = root / "dist"
        output.mkdir()
        (output / "index.html").write_text("<p>ok</p>", encoding="utf-8")


def test_doctor_help_succeeds() -> None:
    result = runner.invoke(app, ["doctor", "--help"])

    assert result.exit_code == SUCCESS
    assert "Check whether a local PyPageKit project environment is usable." in _plain(
        result.output
    )


def test_doctor_succeeds_for_complete_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "demo"
    _write_project(root, with_output=True)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["doctor", "demo"])

    assert result.exit_code == SUCCESS
    output = _plain(result.output)
    assert "PyPageKit Doctor" in output
    assert "[PASS] Project metadata: Project name: doctor-demo" in output
    assert "0 failure(s)" in output


def test_doctor_allows_missing_output_as_warning(tmp_path: Path) -> None:
    root = tmp_path / "demo"
    _write_project(root, with_output=False)

    result = runner.invoke(app, ["doctor", str(root)])

    assert result.exit_code == SUCCESS
    output = _plain(result.output)
    assert "[WARNING] dist/" in output
    assert "2 warning(s)" in output


def test_doctor_returns_execution_error_for_invalid_project(tmp_path: Path) -> None:
    root = tmp_path / "empty"
    root.mkdir()

    result = runner.invoke(app, ["doctor", str(root)])

    assert result.exit_code == EXECUTION_ERROR
    assert "[FAIL] pyproject.toml" in _plain(result.output)
