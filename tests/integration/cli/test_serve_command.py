import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pypagekit.cli.app import app
from pypagekit.cli.exit_codes import EXECUTION_ERROR, SUCCESS, USAGE_ERROR
from pypagekit.development import DevelopmentServerConfig, DevelopmentServerInfo

runner = CliRunner()
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(output: str) -> str:
    return _ANSI_RE.sub("", output)


def test_serve_help_succeeds() -> None:
    result = runner.invoke(app, ["serve", "--help"])

    assert result.exit_code == SUCCESS
    output = _plain(result.output)
    assert "Serve generated static output for local development." in output
    assert "--host" in output
    assert "--port" in output


def test_serve_missing_default_root_is_execution_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["serve"])

    assert result.exit_code == EXECUTION_ERROR
    assert "Development server failed:" in result.stderr
    assert "does not exist" in result.stderr


@pytest.mark.parametrize("port", ["0", "65536"])
def test_serve_invalid_cli_port_is_usage_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    port: str,
) -> None:
    root = tmp_path / "dist"
    root.mkdir()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["serve", "--port", port])

    assert result.exit_code == USAGE_ERROR


class _FakeSession:
    def __init__(self, root: Path) -> None:
        self.info = DevelopmentServerInfo(root, "127.0.0.1", 9123)
        self.served = False
        self.closed = False

    def __enter__(self) -> "_FakeSession":
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        del exc_type, exc_value, traceback
        self.closed = True

    def serve_forever(self) -> None:
        self.served = True


def test_serve_delegates_to_development_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "public"
    root.mkdir()
    captured: list[DevelopmentServerConfig] = []
    session = _FakeSession(root)

    def fake_create(
        self: object,
        config: DevelopmentServerConfig,
    ) -> _FakeSession:
        del self
        captured.append(config)
        return session

    monkeypatch.setattr(
        "pypagekit.cli.commands.serve.DevelopmentServer.create",
        fake_create,
    )

    result = runner.invoke(
        app,
        [
            "serve",
            str(root),
            "--host",
            "127.0.0.1",
            "--port",
            "9000",
        ],
    )

    assert result.exit_code == SUCCESS
    config = captured[0]
    assert config.root == root
    assert config.host == "127.0.0.1"
    assert config.port == 9000
    assert session.served
    assert session.closed
    assert "http://127.0.0.1:9123" in result.stdout
