import re
from pathlib import Path

from typer.testing import CliRunner

from pypagekit import __version__
from pypagekit.cli.app import app
from pypagekit.cli.exit_codes import EXECUTION_ERROR, SUCCESS

runner = CliRunner()
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(output: str) -> str:
    return _ANSI_RE.sub("", output)


def test_inspect_help_succeeds() -> None:
    result = runner.invoke(app, ["inspect", "--help"])

    assert result.exit_code == SUCCESS
    assert "Describe a PyPageKit project without executing project code." in _plain(
        result.output
    )


def test_inspect_describes_project(tmp_path: Path) -> None:
    root = tmp_path / "demo"
    root.mkdir()
    (root / "pyproject.toml").write_text(
        '[project]\nname = "inspect-demo"\n',
        encoding="utf-8",
    )
    (root / "site.py").write_text(
        'raise RuntimeError("must never execute")\n',
        encoding="utf-8",
    )
    output = root / "dist"
    output.mkdir()
    (output / "index.html").write_text("<p>ok</p>", encoding="utf-8")

    result = runner.invoke(app, ["inspect", str(root)])

    assert result.exit_code == SUCCESS
    text = _plain(result.output)
    assert "PyPageKit Inspect" in text
    assert "Project name: inspect-demo" in text
    assert f"PyPageKit: {__version__}" in text
    assert "dist/index.html: present" in text


def test_inspect_missing_root_is_execution_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["inspect", str(tmp_path / "missing")])

    assert result.exit_code == EXECUTION_ERROR
    assert "Project inspection failed:" in result.stderr
    assert "does not exist" in result.stderr
